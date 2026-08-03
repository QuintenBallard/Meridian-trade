import pandas as pd
import boto3
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

s3_client = boto3.client("s3")

s3_bucket_name = os.getenv("bucket_name")

s3_csv_key = "raw/meridian_trades.csv"
s3_json_key = "raw/meridian_trades.json"
s3_reference_key = "raw/meridian_reference_data.csv"

csv_object = s3_client.get_object(Bucket=s3_bucket_name, Key=s3_csv_key)
json_object = s3_client.get_object(Bucket=s3_bucket_name, Key=s3_json_key)
reference_object = s3_client.get_object(Bucket=s3_bucket_name, Key=s3_reference_key)

csv_df = pd.read_csv(csv_object['Body'])
json_data = json.loads(json_object['Body'].read().decode('utf-8'))
reference_df = pd.read_csv(reference_object['Body'])

trade_records = []

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

is_identical = csv_df.equals(json_df)

columns = csv_df.columns.to_list()

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

cleaned_csv = normalize_trades(csv_df)
cleaned_json = normalize_trades(json_df)

merged_df = pd.merge(cleaned_csv, reference_df, how="left", left_on="instrument_id", right_on="instrument_id")

print(merged_df.head())
