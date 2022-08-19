/*
These commands transform the data into a timescaleDB hypertable and aggregates all units to monthly data.
*/


-- add timescaledb as extension to postgres
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- drop tables and views to start from scratch
DROP MATERIALIZED VIEW IF EXISTS monthly_energy_source;
DROP TABLE IF EXISTS energy_units_hyper;
CREATE TABLE energy_units_hyper (
    LIKE energy_units INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES
);

-- 'date' cannot be NULL for timescaledb
ALTER TABLE energy_units_hyper ALTER COLUMN date SET NOT NULL;

-- create timescaledb hypertable with 1 month chunks (as we want do display only monthly data)
SELECT create_hypertable('energy_units_hyper', 'date', chunk_time_interval => INTERVAL '1 month');

-- import data
INSERT INTO energy_units_hyper
  SELECT * FROM energy_units;

-- create the materialized view that we will then use in Django (with monthly data as well)
CREATE MATERIALIZED VIEW monthly_energy_source(date, net_nominal_capacity, zip_code, commune, county, state, energy_source)
WITH (timescaledb.continuous) AS
  SELECT timescaledb_experimental.time_bucket_ng('1 month', date) AS bucket, sum(net_nominal_capacity), zip_code, commune, county, state, energy_source
  FROM energy_units_hyper
    GROUP BY bucket, zip_code, commune, county, state, energy_source;
