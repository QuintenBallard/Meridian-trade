from datetime import date

import pandas as pd
import pytest

from data.transform.schema_validation import validate_dataframes


@pytest.fixture
def valid_merged_df():
    return pd.DataFrame(
        {
            "trade_id": ["T1"],
            "instrument_id": ["I1"],
            "instrument_type": ["Bond"],
            "instrument_name": ["Meridian Bond"],
            "quantity": [10],
            "price": [25.0],
            "trade_value": [250.0],
            "batch_id": ["B1"],
            "trade_date": [date(2026, 8, 6)],
            "buyer": ["Firm A"],
            "seller": ["Firm B"],
            "asset_class": ["Fixed Income"],
            "trading_venue": ["NYSE"],
            "issuer": ["Meridian"],
            "currency": ["USD"],
            "status": ["Active"],
            "trade_status": ["Settled"],
        }
    )


@pytest.fixture
def valid_log_df():
    return pd.DataFrame(
        {
            "trade_id": ["T2"],
            "instrument_id": [None],
            "instrument_type": ["Bond"],
            "quantity": [5],
            "price": [10.0],
            "batch_id": ["B1"],
            "trade_date": [date(2026, 8, 6)],
            "buyer": ["Firm A"],
            "seller": ["Firm B"],
            "trade_status": ["Pending"],
            "error_code": ["MISSING_INSTRUMENT_ID"],
            "error_message": ["Trade has no instrument_id"],
        }
    )


@pytest.fixture
def valid_batch_df():
    return pd.DataFrame(
        {
            "batch_id": ["B1"],
            "batch_date": [date(2026, 8, 6)],
            "records_collected": [1],
            "record_failures": [1],
        }
    )


def test_valid_dataframes_pass_validation(
    valid_merged_df,
    valid_log_df,
    valid_batch_df,
):
    trade_df, log_df, batch_df, is_valid = validate_dataframes(
        valid_merged_df,
        valid_log_df,
        valid_batch_df,
    )

    assert is_valid is True
    assert len(trade_df) == 1
    assert len(log_df) == 1
    assert len(batch_df) == 1


def test_negative_price_fails_validation(
    valid_merged_df,
    valid_log_df,
    valid_batch_df,
):
    valid_merged_df.loc[0, "price"] = -25.0

    _, _, _, is_valid = validate_dataframes(
        valid_merged_df,
        valid_log_df,
        valid_batch_df,
    )

    assert is_valid is False


def test_missing_instrument_id_fails_merged_schema(
    valid_merged_df,
    valid_log_df,
    valid_batch_df,
):
    valid_merged_df.loc[0, "instrument_id"] = None

    _, _, _, is_valid = validate_dataframes(
        valid_merged_df,
        valid_log_df,
        valid_batch_df,
    )

    assert is_valid is False


def test_extra_column_fails_strict_schema(
    valid_merged_df,
    valid_log_df,
    valid_batch_df,
):
    valid_merged_df["unexpected_column"] = "unexpected"

    _, _, _, is_valid = validate_dataframes(
        valid_merged_df,
        valid_log_df,
        valid_batch_df,
    )

    assert is_valid is False


def test_duplicate_batch_id_fails_validation(
    valid_merged_df,
    valid_log_df,
    valid_batch_df,
):
    duplicate_batch = pd.concat(
        [valid_batch_df, valid_batch_df],
        ignore_index=True,
    )

    _, _, _, is_valid = validate_dataframes(
        valid_merged_df,
        valid_log_df,
        duplicate_batch,
    )

    assert is_valid is False