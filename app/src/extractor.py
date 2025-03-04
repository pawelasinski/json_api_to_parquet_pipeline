import os
import json
import hashlib
import asyncio
import logging
import random
from datetime import date
from collections import defaultdict

import pandas as pd
import aiohttp
import asyncpg
from aiohttp import ClientError, ClientResponseError
from asyncpg.exceptions import PostgresError

from config import http_configs
from utils import get_date_path_directories
from exceptions import MaximumRetryException

logger = logging.getLogger(__name__)


def get_remote_json_hash(json_content: dict) -> str:
    """Computes the SHA256 hash of the given JSON content.

    Args:
        json_content: JSON content to hash.

    Returns:
        The hexadecimal SHA256 hash.

    """
    return hashlib.sha256(
        json.dumps(json_content, sort_keys=True).encode("utf-8")).hexdigest()


async def check_response(response: aiohttp.ClientResponse) -> None:
    """Asynchronously checks if the HTTP response is valid (i.e. 200).

    Args:
        response: The HTTP response object to the request.

    Raises:
        ClientResponseError: If the response status is not 200.

    """
    if response.status != 200:
        raise ClientResponseError(
            request_info=response.request_info,
            history=response.history,
            status=response.status,
            message=f"HTTP Error: {response.status}",
        )


async def get_http_response(
        session: aiohttp.ClientSession,
        url: str,
) -> aiohttp.ClientResponse:
    """Asynchronously makes GET request and returns the response.

    Args:
        session: The HTTP session.
        url: The URL to request.

    Returns:
        The HTTP response.

    """
    init_delay = http_configs.delay
    for attempt in range(http_configs.retries):
        try:
            response = await session.get(url)
            await check_response(response)
            return response
        except ClientError as e:
            if "HTTP Error: 429" in str(e):
                jitter = random.uniform(0, init_delay)
                extended_delay = init_delay + jitter
                logger.warning(
                    "HTTP 429 received for URL %s. Retrying in %.2f seconds (attempt %d)...",
                    url, extended_delay, attempt)
                await asyncio.sleep(extended_delay)
                init_delay *= http_configs.backoff
            else:
                logger.exception("Error fetching URL %s: %s", url, e)
                raise e
    raise MaximumRetryException(f"Max retries reached for URL: {url}")


async def extract(
        api_url_template: str,
        start_date_range: date,
        yesterday_date: date
) -> dict[date, str]:
    """Asynchronously extracts JSON data for each date in the specified range.

    It extracts data from the API and saves the data locally if changed.

    Args:
        api_url_template: The API URL template with a placeholder for the date.
        start_date_range: The start date of the required date range.
        yesterday_date: The end date of the required date range
            (it is always implied yesterday's date).

    Returns:
        A dictionary mapping each date to the path of the downloaded JSON file.

    """
    all_dates = pd.date_range(start=start_date_range, end=yesterday_date).date.tolist()
    json_to_download = defaultdict(str)

    # conn = await asyncpg.connect(...)
    # rows = await conn.fetch("SELECT * FROM table;")
    # await conn.close()

    try:
        pool = await asyncpg.create_pool(
            database=os.getenv("METADATA_DB"),
            user=os.getenv("USER_METADATA_DB"),
            password=os.getenv("PASSWORD_METADATA_DB"),
            host=os.getenv("HOST_METADATA_DB"),
            min_size=7,
            max_size=14,
            timeout=60
        )
    except PostgresError as e:
        logger.exception("Failed to connect to `metadata_db`: %s", e)
        raise

    semaphore = asyncio.Semaphore(http_configs.max_concurrent_requests)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for particular_date in all_dates:
            formatted_date = particular_date.strftime("%d-%m-%Y")
            url = api_url_template.format(formatted_date)
            tasks.append(process_date(session, pool, particular_date, url, semaphore))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, dict):
                json_to_download.update(result)

    await pool.close()
    return json_to_download


async def process_date(
        session: aiohttp.ClientSession,
        pool: asyncpg.Pool,
        particular_date: date,
        url: str,
        semaphore: asyncio.Semaphore
) -> dict[date, str]:
    """Asynchronously processes a single date.

    It fetches data from the API, checks metadata, and saves the JSON file if necessary.

    Args:
        session: The HTTP session.
        pool: The database connection pool to the `metadata_db`.
        particular_date: The date to extract.
        url: The API URL for the date.
        semaphore: Semaphore limiting the number of concurrent requests.

    Returns:
        A dictionary with the date and path to the JSON file if new data was downloaded,
            otherwise an empty dictionary.

    """
    try:
        async with semaphore:
            response = await get_http_response(session, url)
        json_data = await response.json()
    except ClientError as e:
        logger.exception("Skipping date %s due to error in fetching data: %s",
                         particular_date, e)
        return {}

    remote_hash = get_remote_json_hash(json_data)

    async with pool.acquire() as conn:
        async with conn.transaction():
            try:
                record = await conn.fetchrow("SELECT hash FROM metadata_tbl WHERE file_date = $1",
                                             particular_date)
            except PostgresError as e:
                logger.exception("Error reading metadata for date %s: %s",
                                 particular_date, e)
                return {}
            if record and record.get("hash") == remote_hash:
                logger.info("Data for date %s is already uploaded.", particular_date)
                return {}
            try:
                if record:
                    await conn.execute("UPDATE metadata_tbl SET hash = $1 WHERE file_date = $2",
                                       remote_hash, particular_date)
                    logger.warning("Data for %s has been updated.", particular_date)
                else:
                    await conn.execute("INSERT INTO metadata_tbl (file_date, hash) VALUES ($1, $2)",
                                       particular_date, remote_hash)
                    logger.info("Metadata for date %s has been uploaded.", particular_date)
            except PostgresError as e:
                logger.exception("Error updating/uploading metadata for date %s: %s",
                                 particular_date, e)

    raw_data_dir = os.getenv("RAW_DATA_DIR")
    particular_date_dir_raw_path = get_date_path_directories(
        base_path=raw_data_dir,
        year=particular_date.year,
        month=particular_date.month,
        day=particular_date.day
    )
    os.makedirs(particular_date_dir_raw_path, exist_ok=True)
    path_to_json_file = os.path.join(particular_date_dir_raw_path, "file.json")

    try:
        with open(path_to_json_file, "w", encoding="utf-8") as f_json_out:
            json.dump(json_data, f_json_out)  # type: ignore
        logger.info("Saved JSON for date %s to %s",
                    particular_date, path_to_json_file)
    except TypeError as e:
        logger.exception("JSON serialization error for date %s: %s",
                         particular_date, e)
        return {}
    except Exception as e:
        logger.exception("Error saving JSON file for date %s: %s",
                         particular_date, e)
        return {}

    return {particular_date: path_to_json_file}
