import logging
import sys
from data.insertion.insert_data import load_df_to_db
from data.raw.extraction import upload_files_to_s3
from data.transform.transformation import run_pipeline
from data.transform.schema_validation import validate_dataframes

def main():
    success = upload_files_to_s3()

    if not success:
        logging.info("Data failed to load into S3")
        sys.exit()
    else:
        logging.info("Data Successfully loaded into S3")

    logging.info("Starting Transformation Layer")
    merged_df, log_df, batch_df = run_pipeline()

    logging.info("Validating schemas")
    val_merged_df, val_log_df, val_batch_df, validated = validate_dataframes(merged_df, log_df, batch_df)

    if not validated:
        logging.info("DataFrames failed Schema Validation Layer")
    else:
        logging.info("All Dataframes have a correct Schema")

    logging.info("Entering Data Insertion Layer")
    load_df_to_db(val_merged_df, val_log_df, val_batch_df)

if __name__ == "__main__":
    main()