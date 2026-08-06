import pandas as pd
import boto3
import os
import json
import logging
import sys
from data.raw.extraction import upload_files_to_s3
from uuid import uuid4
from datetime import datetime
from dotenv import load_dotenv

def extract_json_data(json_data):
    """Extract relevant fields from the JSON data and return a DataFrame."""

    trade_records = []

    logging.info("Extracting Data from JSON file")

    for trade in json_data:
        trade_records.append({
            "trade_id": trade["tradeReference"],
            "instrument_id": trade["security"]["securityCode"] or pd.NA,
            "instrument_type": trade["security"]["securityType"],
            "trade_date": trade["executionDate"],
            "buyer": trade["counterparties"]["buyingFirm"] or pd.NA,
            "seller": trade["counterparties"]["sellingFirm"] or pd.NA,
            "quantity": trade["tradeDetails"]["units"],
            "price": trade["tradeDetails"]["executionPrice"],
            "trade_status": trade["tradeDetails"]["settlementStatus"]
        })

    json_df = pd.DataFrame(trade_records)

    return json_df

def parse_trade_date(value):
    """Parse the four date formats found in the trade data."""

    if pd.isna(value):
        return pd.NaT

    formats = [
        "%Y-%m-%d",
        "%Y.%m.%d",
        "%m-%d-%Y",
        "%d/%m/%Y",
    ]

    for date_format in formats:
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue

    return pd.NaT

def normalize_trades(df):
    """Put CSV and JSON records into the same comparable format."""

    df = df.copy()

    columns = df.columns.to_list()

    text_columns = [
        "trade_id",
        "instrument_id",
        "instrument_type",
        "buyer",
        "seller",
        "trade_status",
    ]

    for column in text_columns:
        df[column] = (df[column].astype("string").str.strip().replace("", pd.NA))

    df["trade_date"] = df["trade_date"].apply(parse_trade_date)

    df["quantity"] = pd.to_numeric(df["quantity"],errors="coerce").astype("Int64")

    df["price"] = pd.to_numeric(df["price"], errors="coerce").round(2).astype("Float64")

    return df[columns]

def remove_invalid_trades(df):
    """Separate trades with missing instrument_id into a data-quality log."""

    df = df.copy()

    missing_instrument = df["instrument_id"].isna()

    # Records that will go into the data-quality log
    instrument_data_log_df = df.loc[missing_instrument].copy()

    instrument_data_log_df["error_code"] = "MISSING_INSTRUMENT_ID"
    instrument_data_log_df["error_message"] = "Trade has no instrument_id"

    logging.info(f"Found {len(instrument_data_log_df)} trades with missing instrument_id. These will be logged and removed from the valid trades.")

    # Records allowed to continue through the pipeline
    valid_trades_df = df.loc[~missing_instrument].copy()

    negative_prices = valid_trades_df["price"] < 0
    
    # Records that will go into the data-quality log
    negative_data_log_df = valid_trades_df.loc[negative_prices].copy()
    
    negative_data_log_df["error_code"] = "NEGATIVE_PRICE"
    negative_data_log_df["error_message"] = "Trade has a negative price"

    logging.info(f"Found {len(negative_data_log_df)} trades with negative prices. These will be logged and removed from the valid trades.")

    # Records allowed to continue through the pipeline
    valid_trades_df = valid_trades_df.loc[~negative_prices].copy()

    data_log_df = pd.concat([instrument_data_log_df, negative_data_log_df], ignore_index=True)
    
    return valid_trades_df, data_log_df

def merge_data(df, reference_df):
    """Merge trades with instrument reference data."""

    df = df.copy()
    # Merge trades with instrument reference data
    merged_df = df.merge(reference_df, on="instrument_id", how="left", validate="many_to_one")

    merged_df = merged_df.drop(columns=["instrument_type_x"])
    merged_df = merged_df.rename(columns={"instrument_type_y": "instrument_type"})

    return merged_df

def calculate_trade_value(df):
    """Calculate the trade value for each trade."""
    
    df = df.copy()
    df["trade_value"] = df["quantity"] * df["price"]
    return df

def run_pipeline():

    load_dotenv()

    s3_client = boto3.client("s3")

    s3_bucket_name = os.getenv("bucket_name")

    s3_csv_key = "raw/meridian_trades.csv"
    s3_json_key = "raw/meridian_trades.json"
    s3_reference_key = "raw/meridian_reference_data.csv"

    csv_object = None
    json_object = None
    reference_object = None

    for attempt in range(3):
        try:
            logging.info(f"Attempt {attempt + 1}: Fetching CSV file from S3")
            csv_object = s3_client.get_object(Bucket=s3_bucket_name, Key=s3_csv_key)
            break
        except Exception as e:
            logging.error(f"Error occurred while fetching CSV file from S3: {e}")
            raise

    for attempt in range(3):        
        try:
            logging.info(f"Attempt {attempt + 1}: Fetching JSON file from S3")
            json_object = s3_client.get_object(Bucket=s3_bucket_name, Key=s3_json_key)
            break
        except Exception as e:
            logging.error(f"Error occurred while fetching JSON file from S3: {e}")
            raise

    for attempt in range(3):        
        try:
            logging.info(f"Attempt {attempt + 1}: Fetching reference data from S3")
            reference_object = s3_client.get_object(Bucket=s3_bucket_name, Key=s3_reference_key)
            break
        except Exception as e:
            logging.error(f"Error occurred while fetching reference data from S3: {e}")
            raise

    json_data = json.loads(json_object['Body'].read().decode('utf-8'))

    json_df = extract_json_data(json_data)

    if json_df.empty:
        logging.warning("No valid trades found in the JSON file.")

    if len(json_df) < 100000:
        logging.warning(f"JSON file contains only {len(json_df)} trades, which is less than the expected 100,000 trades.")

    logging.info("Reading CSV file...")
    csv_df = pd.read_csv(csv_object['Body'])

    if csv_df.empty:
        logging.warning("No valid trades found in the CSV file.")

    if len(csv_df) < 100000:
        logging.warning(f"CSV file contains only {len(csv_df)} trades, which is less than the expected 100,000 trades.")

    logging.info("Reading reference data...")
    reference_df = pd.read_csv(reference_object['Body'])

    logging.info("Normalizing trade data...")
    cleaned_csv = normalize_trades(csv_df)
    cleaned_json = normalize_trades(json_df)

    logging.info("Removing invalid trades...")
    cleaned_csv, csv_log_df = remove_invalid_trades(cleaned_csv)
    cleaned_json, json_log_df = remove_invalid_trades(cleaned_json)

    if cleaned_csv.equals(cleaned_json):
        logging.info("CSV and JSON trades are identical after cleaning.")
    else:
        sys.exit("CSV and JSON trades are not identical after cleaning. Exiting the pipeline.")
        
    logging.info("Merging data...")
    merged_df = merge_data(cleaned_csv, reference_df)

    logging.info("Calculating trade value...")
    merged_df = calculate_trade_value(merged_df)

    batch_id = str(uuid4())

    merged_df["batch_id"] = batch_id
    csv_log_df["batch_id"] = batch_id

    batch_df = pd.DataFrame({"batch_id": [batch_id], "batch_date": datetime.today()})
    batch_df["records_collected"] = len(merged_df)
    batch_df["record_failures"] = len(csv_log_df)

    logging.info("Finished processing data.")
    return merged_df, csv_log_df, batch_df

if __name__ == "__main__":
    merged_df, csv_log_df, batch_df = run_pipeline()