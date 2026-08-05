CREATE SCHEMA IF NOT EXISTS meridian;

CREATE TABLE IF NOT EXISTS meridian.batch (
    batch_id UUID PRIMARY KEY,
    batch_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS meridian.trade_data (
    trade_record_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    trade_id VARCHAR(100) NOT NULL,
    instrument_id VARCHAR(100) NOT NULL,
    instrument_type VARCHAR(100) NOT NULL,
    instrument_name VARCHAR(255) NOT NULL,
    quantity BIGINT NOT NULL,
    price NUMERIC(18, 2) NOT NULL,
    trade_value NUMERIC(20, 2) NOT NULL,
    batch_id UUID NOT NULL,
    trade_date DATE NOT NULL,
    buyer VARCHAR(255),
    seller VARCHAR(255),
    asset_class VARCHAR(100) NOT NULL,
    trading_venue VARCHAR(150) NOT NULL,
    issuer VARCHAR(255) NOT NULL,
    currency VARCHAR(10) NOT NULL,
    status VARCHAR(50) NOT NULL,
    trade_status VARCHAR(50) NOT NULL,

    CONSTRAINT fk_trade_data_batch
        FOREIGN KEY (batch_id)
        REFERENCES meridian.batch (batch_id),

    CONSTRAINT chk_quantity_positive
        CHECK (quantity > 0),

    CONSTRAINT chk_price_positive
        CHECK (price > 0),

    CONSTRAINT chk_trade_value_positive
        CHECK (trade_value > 0)
);

CREATE TABLE IF NOT EXISTS meridian.trade_error_log (
    log_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    trade_id VARCHAR(100),
    instrument_id VARCHAR(100),
    instrument_type VARCHAR(100),
    quantity BIGINT,
    price NUMERIC(18, 2),
    batch_id UUID,
    trade_date DATE,
    buyer VARCHAR(255),
    seller VARCHAR(255),
    trade_status VARCHAR(50),
    error_code VARCHAR(100),
    error_message TEXT,

    CONSTRAINT fk_trade_error_log_batch
        FOREIGN KEY (batch_id)
        REFERENCES meridian.batch (batch_id)
);