import os
import argparse
import asyncio
import logging
from datetime import datetime, timedelta

from extractor import extract
from transformer import transform_json_to_parquet

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/json_api_to_parquet.log", mode="w"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Main function to extract JSON data from the API and convert it to Parquet format."""
    parser = argparse.ArgumentParser(
        description="The Python script for downloading JSON data over API and saving it to Parquet."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Data for the last N days."
    )

    args = parser.parse_args()

    os.makedirs(os.getenv("RAW_DATA_DIR"), exist_ok=True)
    os.makedirs(os.getenv("PROCESSED_DATA_DIR"), exist_ok=True)

    yesterday_date = datetime.today().date() - timedelta(days=1)
    start_date_range = yesterday_date - timedelta(days=args.days - 1)

    api_url_template = "https://api.coingecko.com/api/v3/coins/bitcoin/history?date={}"

    json_to_download = await extract(api_url_template, start_date_range, yesterday_date)

    await transform_json_to_parquet(json_to_download)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception("An unexpected error occurred: %s", e)
        exit(1)
