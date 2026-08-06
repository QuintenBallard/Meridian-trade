import sqlalchemy as sa
import pandas as pd
import time
import logging
from data.insertion.engine import engine
from data.transform.schema_validation import validate_dataframes

eg = engine

trade_df, log_df, batch_df, validated = validate_dataframes()

def load_df_to_db():
    if not validated:
        raise ValueError("DataFrames failed schema validation. Load Cancelled.")

    for attempt in range(3):
        try:
            with eg.begin() as connection:

                logging.info("Inserting Batch Dataframe into Meridian-DB")
                batch_df.to_sql(
                    name="batch",
                    con=connection,
                    schema="meridian",
                    if_exists="append",
                    index=False,
                    chunksize=1000,
                    method="multi",
                )

                logging.info("Inserting Trade_data Dataframe into Meridian-DB")
                trade_df.to_sql(
                    name="trade_data",
                    con=connection,
                    schema="meridian",
                    if_exists="append",
                    index=False,
                    method="multi",
                )

                logging.info("Inserting Trade_error_log Dataframe into Meridian-DB")
                log_df.to_sql(
                    name="trade_error_log",
                    con=connection,
                    schema="meridian",
                    if_exists="append",
                    index=False,
                    chunksize=1000,
                    method="multi",
                )

            logging.info("Data loaded successfully.")
            break

        except sa.exc.SQLAlchemyError as error:
            logging.info(f"Database load attempt {attempt + 1} failed:")
            logging.error(error)

            if attempt == 2:
                logging.error("Database load failed after 3 attempts.")
                raise

            time.sleep(2)


if __name__ == "__main__":
    load_df_to_db()