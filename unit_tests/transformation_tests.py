from datetime import date

import pandas as pd
import pytest

from data.transform.transformation import (
    calculate_trade_value,
    merge_data,
    parse_trade_date,
    remove_invalid_trades,
)


@pytest.mark.parametrize(
    ("raw_date", "expected"),
    [
        ("2026-08-06", date(2026, 8, 6)),
        ("2026.08.06", date(2026, 8, 6)),
        ("08-06-2026", date(2026, 8, 6)),
        ("06/08/2026", date(2026, 8, 6)),
    ],
)
def test_parse_trade_date_accepts_supported_formats(raw_date, expected):
    assert parse_trade_date(raw_date) == expected


@pytest.mark.parametrize("raw_date", [None, "", "not-a-date"])
def test_parse_trade_date_returns_nat_for_invalid_values(raw_date):
    assert pd.isna(parse_trade_date(raw_date))


def test_remove_invalid_trades_separates_bad_records():
    trades = pd.DataFrame(
        {
            "trade_id": ["T1", "T2", "T3"],
            "instrument_id": ["I1", pd.NA, "I3"],
            "price": [10.0, 20.0, -5.0],
        }
    )

    valid, errors = remove_invalid_trades(trades)

    assert valid["trade_id"].tolist() == ["T1"]
    assert set(errors["error_code"]) == {
        "MISSING_INSTRUMENT_ID",
        "NEGATIVE_PRICE",
    }


def test_merge_data_uses_reference_instrument_type():
    trades = pd.DataFrame(
        {
            "trade_id": ["T1"],
            "instrument_id": ["I1"],
            "instrument_type": ["Untrusted value"],
        }
    )
    reference = pd.DataFrame(
        {
            "instrument_id": ["I1"],
            "instrument_type": ["Bond"],
            "instrument_name": ["Example Bond"],
        }
    )

    result = merge_data(trades, reference)

    assert result.loc[0, "instrument_type"] == "Bond"
    assert result.loc[0, "instrument_name"] == "Example Bond"


def test_merge_rejects_duplicate_reference_ids():
    trades = pd.DataFrame(
        {
            "instrument_id": ["I1"],
            "instrument_type": ["Bond"],
        }
    )
    reference = pd.DataFrame(
        {
            "instrument_id": ["I1", "I1"],
            "instrument_type": ["Bond", "Bond"],
        }
    )

    with pytest.raises(pd.errors.MergeError):
        merge_data(trades, reference)


def test_calculate_trade_value():
    trades = pd.DataFrame({"quantity": [5], "price": [12.50]})

    result = calculate_trade_value(trades)

    assert result.loc[0, "trade_value"] == 62.50
    assert "trade_value" not in trades.columns