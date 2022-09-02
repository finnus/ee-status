/*
These commands transform the data into a timescaleDB hypertable and aggregates all units to monthly data.
*/


-- add timescaledb as extension to postgres
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- drop tables and views to start from scratch
DROP MATERIALIZED VIEW IF EXISTS monthly_timeline;
DROP TABLE IF EXISTS energy_units_hyper;
CREATE TABLE energy_units_hyper
(
    LIKE energy_units INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES
);

-- 'date' cannot be NULL for timescaledb
ALTER TABLE energy_units_hyper
    ALTER COLUMN date SET NOT NULL;

-- create timescaledb hypertable with 1 month chunks (as we want do display only monthly data)
SELECT create_hypertable('energy_units_hyper', 'date', chunk_time_interval => INTERVAL '1 month');

-- import data
INSERT INTO energy_units_hyper
SELECT *
FROM energy_units;

-- create the materialized view that we will then use in Django (with monthly data as well)
CREATE MATERIALIZED VIEW monthly_timeline
            (date, zip_code, commune, county, state, energy_source, net_nominal_capacity)
            WITH (timescaledb.continuous)
AS
SELECT timescaledb_experimental.time_bucket_ng('1 month', date) AS bucket,
       zip_code,
       commune,
       county,
       state,
       energy_source,
       sum(net_nominal_capacity)
FROM energy_units_hyper
GROUP BY bucket, zip_code, commune, county, state, energy_source;


-- transform into table for django
DROP TABLE IF EXISTS monthly_timeline_table;
CREATE TABLE monthly_timeline_table
(
    LIKE monthly_timeline INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES
);

INSERT INTO monthly_timeline_table (date, zip_code, commune, county, state, energy_source, net_nominal_capacity )
SELECT date,
       zip_code,
       commune,
       county,
       state,
       energy_source,
       sum(net_nominal_capacity)
FROM monthly_timeline
GROUP BY date, zip_code, commune, county, state, energy_source;

-- add indexes for faster searching
CREATE INDEX state_idx ON monthly_timeline_table (state);
CREATE INDEX county_idx ON monthly_timeline_table (county);
CREATE INDEX commune_idx ON monthly_timeline_table (commune);
CREATE INDEX zip_code_idx ON monthly_timeline_table (zip_code);

-- add ID column (needed by Django)
ALTER TABLE monthly_timeline_table
    ADD COLUMN id SERIAL PRIMARY KEY;



DROP TABLE IF EXISTS current_totals;
CREATE TABLE current_totals
(
    id                   SERIAL PRIMARY KEY,
    zip_code             VARCHAR(6),
    commune              VARCHAR(200),
    county               VARCHAR(200),
    state                VARCHAR(200),
    energy_source        VARCHAR(50),
    net_nominal_capacity NUMERIC(20, 2)
);

INSERT INTO current_totals (zip_code, commune, county, state, energy_source, net_nominal_capacity)
SELECT zip_code, commune, county, state, energy_source, sum(net_nominal_capacity)
FROM monthly_timeline
GROUP BY zip_code, commune, county, state, energy_source;

CREATE INDEX totals_state_idx ON current_totals (state);
CREATE INDEX totals_county_idx ON current_totals (county);
CREATE INDEX totals_commune_idx ON current_totals (commune);
CREATE INDEX totals_zip_code_idx ON current_totals (zip_code);
