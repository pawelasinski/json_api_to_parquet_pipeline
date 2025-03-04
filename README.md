# JSON API to Parquet Pipeline

This mini-project implements an asynchronous ELT data pipeline for extracting JSON data (the Bitcoin exchange rate on a
specific date range) from [CoinGecko](https://www.coingecko.com) API, storing metadata in PostgreSQL, and transforming
the JSON data into Parquet format.
The pipeline leverages Python's asynchronous capabilities (aiohttp, asyncpg) to efficiently handle I/O‑bound tasks and
data processing libraries (pandas, pyarrow).
The entire solution is containerized using Docker and Docker Compose.

## Features

- Concurrently downloads JSON data from API for a configurable date range.
- Utilized PostgreSQL to store the JSON's metadata to prevent redundant downloads.
- Converts downloaded JSON files into efficient Parquet format.

## Prerequisites

- Docker
- Docker Compose

## Installation and Execution

1. **Clone the repository**:
   ```bash
   git clone git@github.com:pawelasinski/json_to_parquet_pipeline.git
   cd json_to_parquet_pipeline
   ```

2. **Create and populate the `.env` file**:
   ```env
   RAW_DATA_DIR=raw_data
   PROCESSED_DATA_DIR=data
   
   METADATA_DB=metadata_db
   USER_METADATA_DB=<username>
   PASSWORD_METADATA_DB=<password>
   HOST_METADATA_DB=metadata_postgres_db
   ```

3. **Build and run the pipeline**:
   ```bash
   docker compose up --build -d
   ```
   ```bash
   python src/main.py --days N
   ```
   where `N` represents the number of days to process (e.g., `--days 3` will process data for the last 3 days, starting
   from yesterday). It defaults to `7`.
   > N.B. The application operates in GMT.
    - The application extracts data from the API, stores JSON and metadata, and converts JSON to Parquet.
    - Raw (JSON files) data are downloaded into the `raw_data` directory, organized by date into subdirectories (e.g.,
      `raw_data/year=2025/month=3/day=3/file.json`). Once downloaded, the pipeline transforms these files into Parquet
      format and stores them in the `data` directory using a similar date-based structure.
    - Logs are generated in the `logs/` directory.

4. **Stop the containers**:
   ```bash
   docker compose down
   ```
    - To remove volumes as well, add the flag `--volumes`: `docker compose down --volumes`.

## Project File Structure

```text
json_api_to_parquet_pipeline/
├── app/                          # Application code
│   ├── Dockerfile                # Dockerfile for the ELT pipeline app
│   └── src/
│       ├── config.py                   # Configuration settings
│       ├── exceptions.py               # Custom exceptions for error handling
│       ├── extractor.py                # Extraction logic for fetching JSON data
│       ├── transformer.py              # Transformation logic from JSON to Parquet
│       ├── main.py                     # Main entry point of the ELT pipeline app
│       └── utils.py                    # Utility functions (e.g., date-based paths)
├── metadata_db/                  # PostgreSQL metadata database
│   ├── Dockerfile                  # Dockerfile for the `metadata_postgres_db` container
│   └── init_db.sh                  # Script to initialize the `metadata_db` schema
├── tests/                        # Test code
│   ├── ...                         # ...
│   └── ...                         # ...
├── raw_data/                     # Raw data directory (created automatically)
├── data/                         # Processed data directory (created automatically)
├── logs/                         # Logs (created automatically)
│   └── json_api_to_parquet.log     # Application logs (created automatically)
├── .env                          # Environment variable definitions
├── docker-compose.yml            # Docker Compose configuration for multi-container setup
├── requirements.txt              # Python dependencies
└── README.md                     # Project description
```

## Example Logs

```
2025-03-02 21:20:24,402 - INFO - Data for date 2025-02-28 is already uploaded.
2025-03-02 21:18:36,923 - INFO - Metadata for date 2025-03-02 has been uploaded.
2025-03-02 21:18:36,928 - INFO - Saved JSON for date 2025-03-02 to raw_data/year=2025/month=3/day=2/file.json
2025-03-02 21:18:37,101 - INFO - Metadata for date 2025-03-01 has been uploaded.
2025-03-02 21:18:37,106 - INFO - Saved JSON for date 2025-03-01 to raw_data/year=2025/month=3/day=1/file.json
2025-03-02 21:18:58,340 - INFO - Converted JSON to Parquet for date 2025-03-02 and saved to data/year=2025/month=3/day=2/file.parquet
2025-03-02 21:18:58,340 - INFO - Converted JSON to Parquet for date 2025-03-01 and saved to data/year=2025/month=3/day=1/file.parquet
```

## Possible Project Extensions

- Expand the retry logic to handle additional HTTP errors (such as 500-series) and potential database failures.  
- Move the date format, endpoint, and other hardcoded parameters to configuration files or allow them to be passed via CLI for more flexible settings management without modifying the source code.  
- Optimize asynchronous code to remove bottlenecks and improve performance.  
- Refactor the code using OOP principles to make it more modular, structured, and easier to maintain and extend, and support SCD Type 2.
- Implement tests with `pytest` to validate the logic and prevent unexpected issues.
- Deploy the pipeline in Airflow with a scheduled execution (e.g., daily or weekly) to automate the workflow.  
- Integrate a Dockerized storage solution like HDFS or MinIO to reliably and efficiently store processed data, considering the challenges of handling many small files.  
- Leverage Spark for data processing to ensure efficient handling of large datasets.

## License

[MIT License](./LICENSE)

## Author

Pawel Asinski (pawel.asinski@gmail.com)
