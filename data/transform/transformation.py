import pandas as pd
import boto3
import os
import json
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

csv_data = pd.read_csv(csv_object['Body'])
json_data = json.loads(json_object['Body'].read().decode('utf-8'))
reference_data = pd.read_csv(reference_object['Body'])

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

csv_df = pd.DataFrame(csv_data)
reference_df = pd.DataFrame(reference_data)
json_df = pd.DataFrame(trade_records)

print(csv_df.head())
print(json_df.head())
