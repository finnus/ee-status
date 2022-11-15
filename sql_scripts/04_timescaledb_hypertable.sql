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
            (date, municipality_key, municipality, county, state, pv_net_nominal_capacity, wind_net_nominal_capacity,
             biomass_net_nominal_capacity, hydro_net_nominal_capacity)
            WITH (timescaledb.continuous)
AS
SELECT timescaledb_experimental.time_bucket_ng('1 month', date) AS bucket,
       municipality_key,
       municipality,
       county,
       state,
       sum(pv_net_nominal_capacity),
       sum(wind_net_nominal_capacity),
       sum(biomass_net_nominal_capacity),
       sum(hydro_net_nominal_capacity)
FROM energy_units_hyper
GROUP BY bucket, municipality_key, municipality, county, state;



-- transform into table for django
DROP TABLE IF EXISTS monthly_timeline_table;
CREATE TABLE monthly_timeline_table
(
    LIKE monthly_timeline INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES
);

INSERT INTO monthly_timeline_table (date, municipality_key, municipality, county, state, pv_net_nominal_capacity,
                                    wind_net_nominal_capacity, biomass_net_nominal_capacity, hydro_net_nominal_capacity)
SELECT date,
       municipality_key,
       municipality,
       county,
       state,
       pv_net_nominal_capacity,
       wind_net_nominal_capacity,
       biomass_net_nominal_capacity,
       hydro_net_nominal_capacity
FROM monthly_timeline;

-- add indexes for faster searching
CREATE INDEX state_idx ON monthly_timeline_table (state);
CREATE INDEX county_idx ON monthly_timeline_table (county);
CREATE INDEX municipality_idx ON monthly_timeline_table (municipality);
CREATE INDEX municipality_key_idx ON monthly_timeline_table (municipality_key);

-- add ID column (needed by Django)
ALTER TABLE monthly_timeline_table
    ADD COLUMN id SERIAL PRIMARY KEY;

DROP TABLE IF EXISTS current_totals;
CREATE TABLE current_totals
(
    id                                 SERIAL PRIMARY KEY,
    municipality_key                   VARCHAR(8),
    municipality                       VARCHAR(200),
    county                             VARCHAR(200),
    state                              VARCHAR(200),
    pv_net_nominal_capacity            NUMERIC(20, 2),
    wind_net_nominal_capacity          NUMERIC(20, 2),
    biomass_net_nominal_capacity       NUMERIC(20, 2),
    hydro_net_nominal_capacity         NUMERIC(20, 2),
    total_net_nominal_capacity         NUMERIC(20, 2),
    population                         INTEGER,
    area                               NUMERIC(20,2)
);

INSERT INTO current_totals (municipality_key, municipality, county, state, pv_net_nominal_capacity,
                            wind_net_nominal_capacity, biomass_net_nominal_capacity, hydro_net_nominal_capacity)
SELECT municipality_key,
       municipality,
       county,
       state,
       sum(pv_net_nominal_capacity),
       sum(wind_net_nominal_capacity),
       sum(biomass_net_nominal_capacity),
       sum(hydro_net_nominal_capacity)
FROM monthly_timeline
GROUP BY municipality_key, municipality, county, state;

CREATE INDEX totals_state_idx ON current_totals (state);
CREATE INDEX totals_county_idx ON current_totals (county);
CREATE INDEX totals_municipality_idx ON current_totals (municipality);
CREATE INDEX totals_municipality_key_idx ON current_totals (municipality_key);

UPDATE current_totals
SET population = (SELECT population FROM municipality_keys WHERE municipality_key = current_totals.municipality_key);

UPDATE current_totals
SET area = (SELECT area FROM municipality_keys WHERE municipality_key = current_totals.municipality_key);
;

UPDATE current_totals
SET total_net_nominal_capacity = coalesce(pv_net_nominal_capacity, 0) + coalesce(wind_net_nominal_capacity, 0) +coalesce(biomass_net_nominal_capacity, 0) +coalesce(hydro_net_nominal_capacity, 0)
;
