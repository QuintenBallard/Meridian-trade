import boto3
import os
from dotenv import load_dotenv
import google.auth
import time
import logging
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

#Upload the CSV and JSON files to the S3 bucket
def upload_files_to_s3():
    """Uploads the CSV and JSON files to the S3 bucket."""
    #Load environment variables from .env file
    load_dotenv()

    #Authenticate with Google Drive API
    credentials, _ = google.auth.default(scopes=SCOPES)
    drive = build("drive", "v3", credentials=credentials)

    #Get the file IDs from environment variables
    csv_file_id = os.getenv("csv_file_id")
    json_file_id = os.getenv("json_file_id")
    reference_data_id = os.getenv("reference_data_id")

    bucket_name = os.getenv("bucket_name")
    csv_key = "raw/meridian_trades.csv"
    json_key = "raw/meridian_trades.json"
    reference_key = "raw/meridian_reference_data.csv"
    
    retries = 3

    #Start S3 Client
    s3_client = boto3.client("s3")

    csv_file = None
    for attempt in range(retries):
        try:
            logging.info(f"Fetching CSV file from Google Drive with file ID: {csv_file_id}")
            csv_file = drive.files().get_media(fileId=csv_file_id).execute()
        except Exception as e:
            logging.error(f"Error occurred while fetching CSV file: {e}")
            time.sleep(2)

    logging.info(f"Uploading CSV file to S3 bucket: {bucket_name}")
    for attempt in range(retries):
        try:
            logging.info(f"Uploading CSV file to S3 bucket: {bucket_name} with key: {csv_key}")
            s3_client.put_object(Body=csv_file, Bucket=bucket_name, Key=csv_key, ContentType="text/csv")
            logging.info(f"CSV file uploaded to S3 bucket: {bucket_name} with key: {csv_key}")
            break
        except Exception as e:
            logging.error(f"Error occurred while uploading CSV file to S3: {e}")
            time.sleep(2)

    json_file = None
    for attempt in range(retries):
        try:
            json_file = drive.files().get_media(fileId=json_file_id).execute()
        except Exception as e:
            logging.error(f"Error occurred while fetching JSON file: {e}")
            time.sleep(2)

    logging.info(f"Uploading JSON file to S3 bucket: {bucket_name}")
    for attempt in range(retries):
        try:
            logging.info(f"Uploading JSON file to S3 bucket: {bucket_name} with key: {json_key}")
            s3_client.put_object(Body=json_file, Bucket=bucket_name, Key=json_key, ContentType="application/json")
            logging.info(f"JSON file uploaded to S3 bucket: {bucket_name} with key: {json_key}")
            break
        except Exception as e:
            logging.error(f"Error occurred while uploading JSON file to S3: {e}")
            time.sleep(2)
    
    reference_data = None
    for attempt in range(retries):
        try:
            reference_data = drive.files().get_media(fileId=reference_data_id).execute()
        except Exception as e:
            logging.error(f"Error occurred while fetching reference data: {e}")
            time.sleep(2)

    logging.info(f"Uploading Reference Data to S3 bucket: {bucket_name}")
    for attempt in range(retries):
        try:
            logging.info(f"Uploading Reference Data to S3 bucket: {bucket_name} with key: {reference_key}")
            s3_client.put_object(Body=reference_data, Bucket=bucket_name, Key=reference_key, ContentType="text/csv")
            logging.info(f"Reference Data uploaded to S3 bucket: {bucket_name} with key: {reference_key}")
            break
        except Exception as e:
            logging.error(f"Error occurred while uploading Reference Data to S3: {e}")
            time.sleep(2)

    #Close the S3 client
    s3_client.close()

def main():
    upload_files_to_s3()

if __name__ == "__main__":
    main()