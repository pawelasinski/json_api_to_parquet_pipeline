import os
import asyncio
import logging
from datetime import date
from json.decoder import JSONDecodeError

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from utils import get_date_path_directories

logger = logging.getLogger(__name__)


async def transform_json_to_parquet(dct_jsons: dict[date, str]) -> None:
    """Asynchronously transforms downloaded JSON files into Parquet format and saves them.

    Args:
        dct_jsons: Dictionary mapping dates to JSON file paths.

    """

    # asyncio.create_task(async_task()): for `async` code, in event loop
    # asyncio.to_thread(sync_task()): for `sync` code and blocking code, in a separate thread

    tasks = []
    for file_date, path_to_json_file in dct_jsons.items():
        tasks.append(asyncio.to_thread(process_file, file_date, path_to_json_file))
    await asyncio.gather(*tasks)


def process_file(file_date: date, path_to_json_file: str) -> None:
    """Synchronously transforms a single JSON file into Parquet format and saves them.

    Args:
        file_date: The date associated with the file.
        path_to_json_file: The file path to the JSON file.

    """
    try:
        df = pd.read_json(path_to_json_file)
    except JSONDecodeError as e:
        logger.exception("JSON serialization error with %s: %s",
                         path_to_json_file, e)
        return
    except Exception as e:
        logger.exception("Error reading JSON file %s: %s",
                          path_to_json_file, e)
        return

    # This clause is necessary to avoid trouble during JSON-Parquet converting.
    # The `market_data` column often contains nested JSON objects or complex types
    # that pyarrow cannot handle directly. Converting it to a string ensures the data
    # is flattened and avoids conversion errors.
    # P.S. I know it's terrible to hardcode like this, but please allow me to leave it here
    # until the moment when I figure out how to handle this case more professionally.
    if "market_data" in df.columns:
        df["market_data"] = df["market_data"].astype(str)

    processed_data_dir = os.getenv("PROCESSED_DATA_DIR")
    particular_date_dir_processed_path = get_date_path_directories(
        base_path=processed_data_dir,
        year=file_date.year,
        month=file_date.month,
        day=file_date.day)
    os.makedirs(particular_date_dir_processed_path, exist_ok=True)
    path_to_parquet_file = os.path.join(particular_date_dir_processed_path, "file.parquet")

    try:
        table = pa.Table.from_pandas(df)
        pq.write_table(table, path_to_parquet_file)
        logger.info("Converted JSON to Parquet for date %s and saved to %s",
                     file_date, path_to_parquet_file)
    except pa.ArrowInvalid as e:
        logger.exception("Error writing Parquet file for date %s: %s",
                          file_date, e)
        return
