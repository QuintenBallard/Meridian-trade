from unittest.mock import MagicMock, Mock, call

import pandas as pd
import pytest
import sqlalchemy as sa

from data.insertion import insert_data


def make_dataframe_mock(row_count):
    dataframe = MagicMock(spec=pd.DataFrame)
    dataframe.__len__.return_value = row_count
    return dataframe


def make_transaction(connection):
    transaction = MagicMock()
    transaction.__enter__.return_value = connection
    transaction.__exit__.return_value = False
    return transaction


def test_load_df_to_db_inserts_all_dataframes(monkeypatch):
    trade_df = make_dataframe_mock(100)
    log_df = make_dataframe_mock(5)
    batch_df = make_dataframe_mock(1)

    connection = Mock()
    transaction = make_transaction(connection)

    mock_engine = Mock()
    mock_engine.begin.return_value = transaction

    monkeypatch.setattr(insert_data, "eg", mock_engine)

    insert_data.load_df_to_db(
        trade_df,
        log_df,
        batch_df,
    )

    mock_engine.begin.assert_called_once()

    batch_df.to_sql.assert_called_once_with(
        name="batch",
        con=connection,
        schema="meridian",
        if_exists="append",
        index=False,
        chunksize=1000,
        method="multi",
    )

    trade_df.to_sql.assert_called_once_with(
        name="trade_data",
        con=connection,
        schema="meridian",
        if_exists="append",
        index=False,
        method="multi",
    )

    log_df.to_sql.assert_called_once_with(
        name="trade_error_log",
        con=connection,
        schema="meridian",
        if_exists="append",
        index=False,
        chunksize=1000,
        method="multi",
    )


def test_dataframes_are_inserted_in_correct_order(monkeypatch):
    trade_df = make_dataframe_mock(100)
    log_df = make_dataframe_mock(5)
    batch_df = make_dataframe_mock(1)

    connection = Mock()
    transaction = make_transaction(connection)

    mock_engine = Mock()
    mock_engine.begin.return_value = transaction

    monkeypatch.setattr(insert_data, "eg", mock_engine)

    writes = Mock()
    writes.attach_mock(batch_df.to_sql, "batch")
    writes.attach_mock(trade_df.to_sql, "trades")
    writes.attach_mock(log_df.to_sql, "errors")

    insert_data.load_df_to_db(
        trade_df,
        log_df,
        batch_df,
    )

    assert writes.mock_calls == [
        call.batch(
            name="batch",
            con=connection,
            schema="meridian",
            if_exists="append",
            index=False,
            chunksize=1000,
            method="multi",
        ),
        call.trades(
            name="trade_data",
            con=connection,
            schema="meridian",
            if_exists="append",
            index=False,
            method="multi",
        ),
        call.errors(
            name="trade_error_log",
            con=connection,
            schema="meridian",
            if_exists="append",
            index=False,
            chunksize=1000,
            method="multi",
        ),
    ]


def test_load_df_to_db_retries_after_database_error(monkeypatch):
    trade_df = make_dataframe_mock(100)
    log_df = make_dataframe_mock(5)
    batch_df = make_dataframe_mock(1)

    connection = Mock()
    successful_transaction = make_transaction(connection)

    mock_engine = Mock()
    mock_engine.begin.side_effect = [
        sa.exc.SQLAlchemyError("First failure"),
        sa.exc.SQLAlchemyError("Second failure"),
        successful_transaction,
    ]

    sleep_mock = Mock()

    monkeypatch.setattr(insert_data, "eg", mock_engine)
    monkeypatch.setattr(insert_data.time, "sleep", sleep_mock)

    insert_data.load_df_to_db(
        trade_df,
        log_df,
        batch_df,
    )

    assert mock_engine.begin.call_count == 3
    assert sleep_mock.call_args_list == [
        call(2),
        call(2),
    ]

    batch_df.to_sql.assert_called_once()
    trade_df.to_sql.assert_called_once()
    log_df.to_sql.assert_called_once()


def test_load_df_to_db_raises_after_three_failures(monkeypatch):
    trade_df = make_dataframe_mock(100)
    log_df = make_dataframe_mock(5)
    batch_df = make_dataframe_mock(1)

    mock_engine = Mock()
    mock_engine.begin.side_effect = sa.exc.SQLAlchemyError(
        "Database unavailable"
    )

    sleep_mock = Mock()

    monkeypatch.setattr(insert_data, "eg", mock_engine)
    monkeypatch.setattr(insert_data.time, "sleep", sleep_mock)

    with pytest.raises(
        sa.exc.SQLAlchemyError,
        match="Database unavailable",
    ):
        insert_data.load_df_to_db(
            trade_df,
            log_df,
            batch_df,
        )

    assert mock_engine.begin.call_count == 3
    assert sleep_mock.call_count == 2

    batch_df.to_sql.assert_not_called()
    trade_df.to_sql.assert_not_called()
    log_df.to_sql.assert_not_called()