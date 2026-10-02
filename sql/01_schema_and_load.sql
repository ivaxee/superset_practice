-- Выполняется автоматически при первом старте контейнера Postgres.
-- Если нужно перезалить данные: docker compose down -v && docker compose up -d

CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE raw.users (
    user_id             BIGINT PRIMARY KEY,
    registered_at       TIMESTAMP NOT NULL,
    platform            TEXT NOT NULL,
    city                TEXT NOT NULL,
    acquisition_channel TEXT NOT NULL
);

CREATE TABLE raw.sessions (
    session_id       BIGINT PRIMARY KEY,
    user_id          BIGINT NOT NULL,
    session_start    TIMESTAMP NOT NULL,
    platform         TEXT NOT NULL,
    added_to_cart    BOOLEAN NOT NULL,
    reached_checkout BOOLEAN NOT NULL,
    made_order       BOOLEAN NOT NULL
);

CREATE TABLE raw.orders (
    order_id   BIGINT PRIMARY KEY,
    user_id    BIGINT NOT NULL,
    session_id BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    platform   TEXT NOT NULL,
    items_cnt  INT NOT NULL,
    amount_rub NUMERIC(10, 2) NOT NULL,
    status     TEXT NOT NULL
);

CREATE TABLE raw.ab_assignments (
    user_id     BIGINT PRIMARY KEY,
    ab_group    TEXT NOT NULL,
    assigned_at TIMESTAMP NOT NULL
);

COPY raw.users          FROM '/data/users.csv'          WITH (FORMAT csv, HEADER true);
COPY raw.sessions       FROM '/data/sessions.csv'       WITH (FORMAT csv, HEADER true);
COPY raw.orders         FROM '/data/orders.csv'         WITH (FORMAT csv, HEADER true);
COPY raw.ab_assignments FROM '/data/ab_assignments.csv' WITH (FORMAT csv, HEADER true);

CREATE INDEX ON raw.sessions (user_id, session_start);
CREATE INDEX ON raw.orders (user_id, created_at);

-- Сюда ты будешь складывать свои витрины (views) для Superset
CREATE SCHEMA IF NOT EXISTS mart;
