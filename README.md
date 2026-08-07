# Meridian Trade ETL Pipeline

## Overview

Meridian Trade ETL Pipeline is a Python data engineering project that collects trade data from Google Drive, stores the raw files in Amazon S3, cleans and validates the data, and loads the final results into a PostgreSQL database.

The project uses three source files:

- Trade data in CSV format
- The same trade data in JSON format
- Reference data for financial instruments

The pipeline first downloads these files from Google Drive and uploads them to S3. It then reads the files from S3, standardizes the CSV and JSON trade records, checks that both formats contain the same cleaned trade data, removes invalid records, joins valid trades to the instrument reference data, and calculates each trade’s total value.

Invalid trades, such as records with a missing instrument ID or a negative price, are separated into an error log instead of being inserted as valid trade records. Each pipeline run also creates a unique batch ID so the loaded data can be connected to the specific run that produced it.

## What Each Part of the Project Does

This project is organized into layers. Each layer has one main job in moving trade data from Google Drive into PostgreSQL.

### `main.py`

This is the main entry point for the project. Running this file starts the full ETL pipeline in this order:

1. Download source files from Google Drive and upload them to Amazon S3.
2. Read and transform the files stored in S3.
3. Validate the transformed data.
4. Insert valid data and error logs into PostgreSQL.

### `data/raw/extraction.py`

This file handles the extraction layer.

It connects to the Google Drive API using read-only access, downloads the CSV, JSON, and instrument reference files, and uploads them into an Amazon S3 bucket.

The raw files are stored with these S3 paths:

- `raw/meridian_trades.csv`
- `raw/meridian_trades.json`
- `raw/meridian_reference_data.csv`

### `data/transform/transformation.py`

This file handles the transformation layer.

It reads the three raw files from S3 and turns them into pandas DataFrames. The JSON trade data is flattened into the same structure as the CSV data. Both trade files are cleaned by standardizing text, dates, quantities, and prices.

The pipeline then:

- Checks that the cleaned CSV and JSON data match.
- Removes trades with missing instrument IDs.
- Removes trades with negative prices.
- Sends invalid records to an error-log DataFrame.
- Joins valid trade records to instrument reference data.
- Calculates `trade_value` by multiplying quantity by price.
- Creates a unique `batch_id` for the pipeline run.

### `data/transform/schema_validation.py`

This file validates the DataFrames before they are inserted into the database.

It uses Pandera to check required columns, expected data types, missing values, unique batch IDs, and rules such as positive quantities, prices, and trade values.

The project validates three DataFrames:

- The valid, enriched trade data
- The invalid-trade error log
- The batch summary data

### `data/insertion/engine.py`

This file creates the connection between Python and PostgreSQL.

It reads the database credentials from the `.env` file and uses SQLAlchemy with the `psycopg2` PostgreSQL driver to create a database engine.

### `data/insertion/insert_data.py`

This file handles the database insertion layer.

It inserts data into PostgreSQL in this order:

1. Batch information goes into `meridian.batch`.
2. Valid trade records go into `meridian.trade_data`.
3. Invalid records go into `meridian.trade_error_log`.

The insert process uses a database transaction and retries up to three times if a SQLAlchemy database error occurs.

### `sql/create_db.sql`

This SQL file creates the PostgreSQL database named `Meridian-DB`.

### `sql/create_schema.sql`

This SQL file creates the `meridian` schema and the tables used by the pipeline:

- `batch` for metadata about each pipeline run
- `trade_data` for valid enriched trade records
- `trade_error_log` for records that failed data-quality checks

### `unit_tests/`

This folder contains tests for the main pipeline layers:

- `extraction_test.py` tests Google Drive and S3 extraction behavior.
- `transformation_tests.py` tests cleaning, validation rules, merging, and trade-value calculations.
- `schema_validation_test.py` tests Pandera schema validation.
- `insert_data_test.py` tests database insertion behavior using mocked database interactions.

## Tech Stack

This project uses Python to build an ETL pipeline that moves trade data from Google Drive to Amazon S3, transforms and validates it, and stores the final results in PostgreSQL.

### Main Technologies

- **Python** — Main programming language used for the ETL pipeline.
- **pandas** — Reads CSV and JSON data, cleans records, merges datasets, and calculates trade values.
- **Amazon S3** — Stores the raw CSV, JSON, and reference-data files before transformation.
- **Google Drive API** — Provides access to the source files stored in Google Drive.
- **PostgreSQL** — Stores batch information, valid trade data, and invalid-record logs.
- **SQLAlchemy** — Connects Python to PostgreSQL and manages database transactions.
- **psycopg2** — PostgreSQL driver used by SQLAlchemy.
- **Pandera** — Validates the structure, data types, and quality rules of the DataFrames before insertion.
- **python-dotenv** — Loads secrets and configuration values from a local `.env` file.
- **pytest** — Used for unit tests.

## Python Dependencies

Install the project dependencies with:

```bash
pip install pandas boto3 google-auth google-api-python-client sqlalchemy psycopg2-binary pandera python-dotenv pytest
```

### Dependency Purpose

| Dependency | Purpose |
|---|---|
| `pandas` | Data cleaning, transformation, merging, and calculations |
| `boto3` | Uploading files to and reading files from Amazon S3 |
| `google-auth` | Authenticating with Google services |
| `google-api-python-client` | Downloading files through the Google Drive API |
| `sqlalchemy` | Creating the PostgreSQL connection and database transaction |
| `psycopg2-binary` | Allowing Python and SQLAlchemy to communicate with PostgreSQL |
| `pandera` | Checking DataFrame schemas and data-quality rules |
| `python-dotenv` | Loading environment variables from `.env` |
| `pytest` | Running unit tests |

> Note: This repository does not currently include a `requirements.txt` or `pyproject.toml` dependency file. Creating a `requirements.txt` later would make setup easier for other users.

## Project Structure

```text
Meridian-trade/
│
├── main.py
├── .env
│
├── data/
│   ├── __init__.py
│   │
│   ├── raw/
│   │   ├── __init__.py
│   │   └── extraction.py
│   │
│   ├── transform/
│   │   ├── __init__.py
│   │   ├── transformation.py
│   │   └── schema_validation.py
│   │
│   └── insertion/
│       ├── engine.py
│       └── insert_data.py
│
├── sql/
│   ├── create_db.sql
│   └── create_schema.sql
│
└── unit_tests/
    ├── extraction_test.py
    ├── transformation_tests.py
    ├── schema_validation_test.py
    └── insert_data_test.py
```

### Root Files

- **`main.py`** — Runs the complete ETL pipeline from extraction through database insertion.
- **`.env`** — Stores configuration values and secrets, including database credentials, S3 bucket information, and Google Drive file IDs. This file should not be committed to Git.

### `data/`

This folder contains the Python code for each ETL layer.

- **`raw/`** — Extracts source files from Google Drive and uploads them to S3.
- **`transform/`** — Reads files from S3, cleans and enriches the data, creates error logs, and validates DataFrames.
- **`insertion/`** — Connects to PostgreSQL and inserts the pipeline output into database tables.

### `sql/`

This folder contains SQL scripts used to prepare PostgreSQL.

- **`create_db.sql`** — Creates the `Meridian-DB` database.
- **`create_schema.sql`** — Creates the `meridian` schema and its tables.

### `unit_tests/`

This folder contains automated tests for the pipeline.

- **`extraction_test.py`** — Tests Google Drive and S3 extraction behavior.
- **`transformation_tests.py`** — Tests the data cleaning, merging, and calculation functions.
- **`schema_validation_test.py`** — Tests the Pandera DataFrame validation rules.
- **`insert_data_test.py`** — Tests database insertion behavior without writing to a real database.

## Setup and Configuration

### 1. Create and activate a virtual environment

```bash
python -m venv venv
```

On Windows PowerShell:

```powershell
\venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
pip install pandas boto3 google-auth google-api-python-client sqlalchemy psycopg2-binary pandera python-dotenv pytest
```

### 2. Configure the `.env` File

Create a `.env` file in the root folder of the project. This file stores configuration values that should not be hardcoded in the Python files.

```env
# Amazon S3
bucket_name=your-s3-bucket-name

# Google Drive file IDs
csv_file_id=your-csv-google-drive-file-id
json_file_id=your-json-google-drive-file-id
reference_data_id=your-reference-data-google-drive-file-id

# PostgreSQL
DB_USER=your_postgres_username
DB_PASS=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=Meridian-DB
```

The pipeline reads the `csv_file_id`, `json_file_id`, and `reference_data_id` values to download the three Google Drive source files.

To find a Google Drive file ID, open the file in Google Drive and copy the value between `/d/` and `/view` in the URL.

> Never commit `.env` to GitHub. It can contain database passwords and identifiers for cloud resources. Add `.env` to `.gitignore` before publishing the repository.

### 3. Configure AWS Credentials and S3

Create an S3 bucket, then place its name in `bucket_name` in the `.env` file.

The AWS account or IAM user running the pipeline needs permission to upload and download objects from that bucket. The pipeline writes and reads these S3 objects:

- `raw/meridian_trades.csv`
- `raw/meridian_trades.json`
- `raw/meridian_reference_data.csv`

Configure AWS credentials locally using the AWS CLI:

```bash
aws configure
```

Enter an AWS access key, secret access key, default AWS Region, and output format when prompted.

### 4. Configure PostgreSQL

Create the PostgreSQL database and tables before running the pipeline.

1. Run `sql/create_db.sql` to create `Meridian-DB`.
2. Connect to the new database.
3. Run `sql/create_schema.sql` to create the `meridian` schema and its tables.
4. Add the correct PostgreSQL connection values to `.env`.

The project connects using the database values in `.env` through SQLAlchemy and `psycopg2`.

### 5. Configure the Google Drive API

The extraction code uses the Google Drive API with the read-only scope:

```text
https://www.googleapis.com/auth/drive.readonly
```

This scope allows the pipeline to view and download the Google Drive source files, but not edit or delete them.

To configure Google Drive access:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a Google Cloud project.
3. Open **APIs & Services** → **Library**.
4. Search for **Google Drive API** and enable it.
5. Configure the OAuth consent screen. Add yourself as a test user if the app is still in testing.
6. In the consent-screen scope settings, add `https://www.googleapis.com/auth/drive.readonly`.
7. Create an OAuth client ID for a **Desktop app** and download its client-secret JSON file.
8. Install the Google Cloud CLI if it is not already installed.
9. From the project folder, authenticate Application Default Credentials (ADC) with the Drive scope:

```powershell
gcloud auth application-default login `
  --client-id-file="C:\path\to\client_secret.json" `
  --scopes="https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/drive.readonly"
```

10. Complete the Google sign-in and consent window using the Google account that can access the three source files.

The Python code uses `google.auth.default(...)`, so it reads the local ADC credentials created by this command.

> If the pipeline receives a Google Drive `403` error saying the request has insufficient authentication scopes, run the ADC login command again with the Drive read-only scope. A previously created credential without that scope cannot gain it automatically.

## How the ETL Pipeline Works

The project follows an ETL process: **Extract, Transform, and Load**.

```text
Google Drive
    ↓
Amazon S3 raw storage
    ↓
pandas transformation and data-quality checks
    ↓
Pandera schema validation
    ↓
PostgreSQL database
```

### 1. Extract Data from Google Drive

The pipeline starts in `main.py` by calling `upload_files_to_s3()`.

The extraction layer:

1. Authenticates with the Google Drive API.
2. Downloads the trade CSV file.
3. Downloads the trade JSON file.
4. Downloads the instrument reference-data CSV file.
5. Uploads each file into the configured Amazon S3 bucket.

The files are stored in S3 before transformation so there is a raw copy of the source data available to the rest of the pipeline.

### 2. Read Raw Data from Amazon S3

The transformation layer reads the three raw files back from S3:

- Trade CSV data
- Trade JSON data
- Instrument reference data

The CSV and reference files are read into pandas DataFrames. The JSON file is parsed and flattened into trade records with the same main fields as the CSV data.

### 3. Clean and Standardize Trade Data

The pipeline cleans the CSV and JSON trade data so both formats can be compared.

It standardizes:

- Text fields, such as trade IDs, instrument IDs, buyers, sellers, and statuses
- Missing or blank values
- Multiple trade-date formats
- Quantities as integer values
- Prices as numeric values rounded to two decimal places

### 4. Check That CSV and JSON Data Match

The project treats the CSV and JSON files as two versions of the same trade dataset.

After cleaning, the pipeline compares them. If they do not match, the pipeline stops rather than loading inconsistent trade data into the database.

### 5. Separate Invalid Trade Records

The pipeline checks for invalid records before loading valid data.

A trade is removed from the valid dataset and added to the error log when it has:

- A missing `instrument_id`
- A negative price

Each invalid record receives an `error_code` and `error_message` explaining why it failed.

### 6. Enrich Trade Data

Valid trades are joined with the instrument reference data by `instrument_id`.

This adds information such as the instrument name, asset class, issuer, currency, trading venue, and status.

The pipeline then calculates:

```text
trade_value = quantity × price
```

### 7. Create Batch Metadata

Each pipeline run creates a unique `batch_id`.

The batch table records:

- The batch ID
- The date of the run
- The number of valid trade records collected
- The number of records that failed data-quality checks

The same batch ID is added to valid trades and error-log records so all database records can be traced back to the run that created them.

### 8. Validate the Final DataFrames

Before database insertion, Pandera validates the three output DataFrames:

- Valid enriched trade data
- Invalid-trade error log
- Batch metadata

The validation checks required columns, data types, null rules, and positive values for quantity, price, and trade value.

### 9. Load Data into PostgreSQL

The final layer inserts the DataFrames into PostgreSQL in this order:

1. Batch metadata is inserted into `meridian.batch`.
2. Valid trade records are inserted into `meridian.trade_data`.
3. Invalid records are inserted into `meridian.trade_error_log`.

All three inserts run in the same database transaction. This means a database error can roll back the transaction instead of leaving only part of a batch loaded.

## Database Schema Design

The project uses a PostgreSQL schema named `meridian`.

```text
meridian.batch
     │
     ├── meridian.trade_data
     │
     └── meridian.trade_error_log
```

The schema separates each pipeline run, valid trade records, and invalid trade records into different tables. This makes it easier to track when data was loaded and why certain records were rejected.

### `meridian.batch`

The `batch` table stores one record for each pipeline run.

| Column | Purpose |
|---|---|
| `batch_id` | Unique ID for the pipeline run. This is the primary key. |
| `batch_date` | Date when the batch was created. |
| `records_collected` | Number of valid trade records in the batch. |
| `record_failures` | Number of records sent to the error log. |

The `batch_id` is used to connect every valid trade and error-log record to the exact ETL run that created it.

### `meridian.trade_data`

The `trade_data` table stores valid, enriched trade records.

| Column Group | Purpose |
|---|---|
| `trade_record_id` | Automatically generated internal primary key for each inserted record. |
| `trade_id` | Trade identifier from the source data. |
| Instrument fields | `instrument_id`, `instrument_type`, `instrument_name`, `asset_class`, `issuer`, and `currency`. |
| Trade fields | `quantity`, `price`, `trade_value`, `trade_date`, and `trade_status`. |
| Party fields | `buyer` and `seller`. |
| Reference fields | `trading_venue` and `status`. |
| `batch_id` | Foreign key connecting the trade to the batch that loaded it. |

The table uses `trade_record_id` as the database primary key instead of relying only on the source `trade_id`. This gives every inserted database row its own unique identifier.

The schema also includes database-level checks to prevent invalid values from being inserted:

- `quantity` must be greater than zero.
- `price` must be greater than zero.
- `trade_value` must be greater than zero.

### `meridian.trade_error_log`

The `trade_error_log` table stores records that failed the project’s data-quality checks.

It keeps available trade details along with:

| Column | Purpose |
|---|---|
| `error_code` | Short identifier for the type of problem, such as `MISSING_INSTRUMENT_ID` or `NEGATIVE_PRICE`. |
| `error_message` | Plain-English description of why the record failed. |
| `batch_id` | Foreign key connecting the error to the pipeline run. |

This design keeps invalid records out of the valid trade table while preserving them for review and troubleshooting.

### Table Relationships

`trade_data.batch_id` and `trade_error_log.batch_id` are foreign keys that reference `batch.batch_id`.

This means:

- A batch can contain many valid trade records.
- A batch can contain many error-log records.
- Every valid trade or logged error can be traced back to one pipeline run.

### Why This Design Was Used

The current schema is a practical ETL design that focuses on pipeline tracking and data quality:

- **Batch table:** Tracks each execution of the pipeline.
- **Trade-data table:** Holds records that passed the quality checks and were enriched with reference data.
- **Error-log table:** Keeps rejected records separate while preserving their details and failure reason.
- **Foreign keys:** Preserve lineage between the batch and the records it produced.
- **Database checks:** Add another layer of protection after the Python validation rules.

The current `trade_data` table is a wide enriched table. Instrument and counterparty details are stored with each trade record rather than in separate normalized tables. This keeps the project simpler for analytics and ETL learning purposes.

## How Data Is Inserted into PostgreSQL

After the trade data is transformed and validated, the pipeline loads the results into PostgreSQL through `data/insertion/insert_data.py`.

The insertion process uses the SQLAlchemy database engine configured in `data/insertion/engine.py`.

### Insert Order

The pipeline inserts data in this order:

```text
1. Batch metadata
2. Valid trade data
3. Invalid-trade error log
```

This order is important because the valid trade and error-log tables both use `batch_id` as a foreign key. The batch record must exist before the related records can be inserted.

### 1. Insert Batch Metadata

The pipeline inserts one batch row into:

```text
meridian.batch
```

This row contains the unique batch ID, batch date, number of valid records, and number of failed records.

```python
batch_df.to_sql(
    name="batch",
    schema="meridian",
    if_exists="append"
)
```

`if_exists="append"` means new pipeline results are added to the table instead of replacing existing batches.

### 2. Insert Valid Trade Records

The pipeline inserts the valid enriched trade DataFrame into:

```text
meridian.trade_data
```

These records have already passed the transformation and data-quality checks. They include the trade details, reference-data fields, calculated trade value, and batch ID.

```python
trade_df.to_sql(
    name="trade_data",
    schema="meridian",
    if_exists="append"
)
```

### 3. Insert Invalid Records into the Error Log

Records with a missing instrument ID or negative price are inserted into:

```text
meridian.trade_error_log
```

The error-log records include the available trade details, the batch ID, an error code, and an error message.

```python
log_df.to_sql(
    name="trade_error_log",
    schema="meridian",
    if_exists="append"
)
```

### Transaction Handling

All three inserts run inside one SQLAlchemy transaction:

```python
with engine.begin() as connection:
```

This is helpful because PostgreSQL treats the group of inserts as one unit of work. If an insertion fails, the transaction can roll back instead of permanently saving only part of a batch.

### Insert Performance Settings

The pipeline uses `method="multi"` for its inserts. This lets pandas send multiple rows in one SQL statement instead of sending one row at a time.

The batch and error-log inserts also use `chunksize=1000`, meaning pandas inserts those DataFrames in groups of up to 1,000 records.

### Retry Behavior

If a SQLAlchemy database error occurs, the insertion layer retries the full database load up to three times. It waits two seconds between attempts.

If all three attempts fail, the error is raised so the failed load is visible instead of being silently ignored.

### Important Note About Validation

The pipeline logs whether Pandera schema validation passed or failed before the insertion step. As the current `main.py` is written, it still calls the insertion function after a validation failure.

For a stronger production version, the pipeline should stop before database insertion when validation returns `False`.

## How to Run the Project

Follow these steps after installing the dependencies and configuring Google Drive, AWS, PostgreSQL, and the `.env` file.

### 1. Activate the Virtual Environment

From the project root folder, activate the Python virtual environment.

On Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Create the PostgreSQL Database

The project database is named `Meridian-DB`.

Run this command in PostgreSQL:

```sql
CREATE DATABASE "Meridian-DB";
```

> PostgreSQL database names with hyphens must be wrapped in double quotes. Also, PostgreSQL does not support `CREATE DATABASE IF NOT EXISTS`, so this command may need to be run manually instead of directly using `sql/create_db.sql`.

### 3. Create the Schema and Tables

Connect to the new database and run:

```powershell
psql -U your_postgres_username -d "Meridian-DB" -f sql/create_schema.sql
```

This creates:

- The `meridian` schema
- The `meridian.batch` table
- The `meridian.trade_data` table
- The `meridian.trade_error_log` table

### 4. Confirm the `.env` File Is Configured

Before running the pipeline, make sure `.env` contains:

- The S3 bucket name
- The three Google Drive file IDs
- PostgreSQL connection values
- AWS credentials configured through the AWS CLI
- Google Application Default Credentials configured with the Drive read-only scope

### 5. Run the ETL Pipeline

From the project root folder, run:

```powershell
python -m main.py
```

The pipeline will:

1. Download the source files from Google Drive.
2. Upload raw copies to Amazon S3.
3. Read the files from S3.
4. Clean and validate the trade data.
5. Separate invalid records into an error log.
6. Insert batch metadata, valid trades, and invalid records into PostgreSQL.

### 6. Run the Unit Tests

To run the test files:

```powershell
pytest unit_tests
```

The unit tests are designed to test individual pipeline layers without depending on live Google Drive, S3, or PostgreSQL resources.

### 7. Check the Loaded Data

After a successful run, connect to PostgreSQL and check the results:

```sql
SELECT * FROM meridian.batch;

SELECT * FROM meridian.trade_data
LIMIT 10;

SELECT * FROM meridian.trade_error_log
LIMIT 10;
```

You can also check how many records were loaded for each batch:

```sql
SELECT
    batch_id,
    records_collected,
    record_failures
FROM meridian.batch;
```

## Troubleshooting

### Google Drive Error: `403` or “insufficient authentication scopes”

This means the local Google Application Default Credentials do not have permission to read Google Drive files.

Run the authentication command again with the Drive read-only scope:

```powershell
gcloud auth application-default login `
  --client-id-file="C:\path\to\client_secret.json" `
  --scopes="https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/drive.readonly"
```

Also confirm that:

- The Google Drive API is enabled in Google Cloud.
- The OAuth consent screen includes the Drive read-only scope.
- The Google account used during login has access to all three source files.
- The file IDs in `.env` are correct.

### Amazon S3 Error: `Bucket=None`

This usually means the S3 bucket name was not loaded correctly from `.env`.

Check that `.env` contains:

```env
bucket_name=your-s3-bucket-name
```

Make sure there are no spelling differences. The code specifically looks for `bucket_name`.

### Amazon S3 Access Denied Error

This means the AWS credentials do not have permission to access the configured bucket.

Check that:

- AWS credentials were configured with `aws configure`.
- The bucket name is correct.
- The IAM user or role can upload and download objects from the S3 bucket.
- The bucket exists in the AWS account and Region you are using.

### Python Error: `ModuleNotFoundError: No module named 'psycopg2'`

Install the PostgreSQL Python driver inside the active virtual environment:

```powershell
pip install psycopg2-binary
```

Then rerun the pipeline.

### PostgreSQL Connection Error

Check the database settings in `.env`:

```env
DB_USER=your_postgres_username
DB_PASS=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=Meridian-DB
```

Also confirm that:

- PostgreSQL is running.
- The database exists.
- The username and password are correct.
- PostgreSQL is listening on the configured port.
- The user has permission to access the database.

### PostgreSQL Error: Schema or Table Does Not Exist

Run the schema SQL file after creating the database:

```powershell
psql -U your_postgres_username -d "Meridian-DB" -f sql/create_schema.sql
```

This creates the `meridian` schema and the required tables.

### CSV and JSON Data Do Not Match

The pipeline stops when the cleaned CSV and JSON trade data are different.

This is intentional. The project expects the CSV and JSON files to be two formats of the same trade dataset. Check that both Google Drive file IDs point to the correct version of the trade data.

### Validation Error

Pandera validation can fail when expected columns are missing, data types are incorrect, or data-quality rules are broken.

Examples include:

- Missing required columns
- A missing `instrument_id` in valid trade data
- Quantity, price, or trade value that is not positive
- Incorrect date or numeric formats

Check the validation error output to identify the failing column and record.

### Important Security Note

Do not upload the following to GitHub:

- `.env`
- PostgreSQL passwords
- AWS access keys
- Downloaded Google OAuth client-secret files
- Google authentication tokens

Add these files to `.gitignore` before making the repository public.