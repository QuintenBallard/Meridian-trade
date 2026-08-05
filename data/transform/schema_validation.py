import pandas as pd
import pandera as pa
import pandera.pandas as pda
from data.transform.transformation import run_pipeline

merged_df, csv_log_df, batch_df = run_pipeline()


merged_df_schema = pa.DataFrameSchema(
    columns={
        "trade_id": pa.Column(pa.String, nullable=False),
        "instrument_id": pa.Column(pa.String, nullable=False),
        "instrument_type": pa.Column(pa.String, nullable=False),
        "instrument_name": pa.Column(pa.String, nullable=False),
        "quantity": pa.Column(pa.Int, pa.Check.greater_than(0), nullable=False),
        "price": pa.Column(pa.Float, pa.Check.greater_than(0.0), nullable=False),
        "trade_value": pa.Column(pa.Float, pa.Check.greater_than(0.0), nullable=False),
        "batch_id": pa.Column(pa.String, nullable=False),
        "trade_date": pa.Column(pa.Date, nullable=False),
        "buyer": pa.Column(pa.String, nullable=True),
        "seller": pa.Column(pa.String, nullable=True),
        "asset_class": pa.Column(pa.String, nullable=False),
        "trading_venue": pa.Column(pa.String, nullable=False),
        "issuer": pa.Column(pa.String, nullable=False),
        "currency": pa.Column(pa.String, nullable=False),
        "status": pa.Column(pa.String, nullable=False),
        "trade_status": pa.Column(pa.String, nullable=False)
    },
    strict=True,
    coerce=True
)

batch_df_schema = pa.DataFrameSchema(
    columns = {
        "batch_id": pa.Column(pa.String, unique=True, nullable=False),
        "batch_date": pa.Column(pa.Date, nullable=False)
    },
    strict=True,
    coerce=True
)

log_df_schema = pa.DataFrameSchema(
    columns = {
        "trade_id": pa.Column(pa.String, nullable=True),
        "instrument_id": pa.Column(pa.String, nullable=True),
        "instrument_type": pa.Column(pa.String, nullable=True),
        "quantity": pa.Column(pa.Int, nullable=True),
        "price": pa.Column(pa.Float, nullable=True),
        "batch_id": pa.Column(pa.String, nullable=True),
        "trade_date": pa.Column(pa.Date, nullable=True),
        "buyer": pa.Column(pa.String, nullable=True),
        "seller": pa.Column(pa.String, nullable=True),
        "trade_status": pa.Column(pa.String, nullable=True),
        "error_code": pa.Column(pa.String, nullable=True),
        "error_message": pa.Column(pa.String, nullable=True)
    },
    strict=True,
    coerce=True
)

def validate_dataframes(merged_df: pd.DataFrame = merged_df, csv_log_df: pd.DataFrame = csv_log_df, batch_df: pd.DataFram = batch_df):
    """Validate all pipeline DataFrames against their Pandera schemas."""

    try:
        validated_merged_df = merged_df_schema.validate(merged_df, lazy=True)

        validated_log_df = log_df_schema.validate(csv_log_df, lazy=True)

        validated_batch_df = batch_df_schema.validate(batch_df,lazy=True)

        print("All DataFrames passed schema validation.")

        return validated_merged_df, validated_log_df, validated_batch_df, True
    
    except pda.errors.SchemaErrors as error:
        print("Schema validation failed:")
        print(error.failure_cases)
        return validated_merged_df, validated_log_df, validated_batch_df, False
