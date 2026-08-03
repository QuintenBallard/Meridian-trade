import boto3
import os
from dotenv import load_dotenv

#Upload the CSV and JSON files to the S3 bucket
def upload_files_to_s3():
    """
    Uploads the CSV and JSON files to the specified S3 bucket.
    """
    #Load environment variables from .env file
    load_dotenv()
        
    #Define the S3 bucket name and file names from environment variables
    bucket_name = os.getenv("bucket_name")
    csv_file = os.getenv("csv_file")
    json_file = os.getenv("json_file")
        
    csv_key = "raw/meridian_trades.csv"
    json_key = "raw/meridian_trades.json"

    #Start S3 Client
    s3_client = boto3.client("s3")
    
    print(f"Uploading {csv_file} to s3://{bucket_name}/{csv_key}")
    s3_client.upload_file(csv_file, bucket_name, csv_key)

    print(f"Uploading {json_file} to s3://{bucket_name}/{json_key}")
    s3_client.upload_file(json_file, bucket_name, json_key)

    #Close the S3 client
    s3_client.close()

def main():
    upload_files_to_s3()

if __name__ == "__main__":
    main()