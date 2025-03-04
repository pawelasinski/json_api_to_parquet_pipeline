#!/usr/bin/env bash

set -e

psql -v ON_ERROR_STOP=1 --username "${USER_METADATA_DB}" --dbname "${METADATA_DB}" <<-EOSQL
CREATE TABLE IF NOT EXISTS metadata_tbl
  (
    file_date DATE PRIMARY KEY,
    hash TEXT
  );
EOSQL
