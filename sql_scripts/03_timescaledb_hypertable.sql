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

ALTER TABLE monthly_timeline
    ADD COLUMN total_net_nominal_capacity NUMERIC(20, 2);

UPDATE monthly_timeline
    SET total_net_nominal_capacity = COALESCE(pv_net_nominal_capacity, 0) + COALESCE(wind_net_nominal_capacity, 0) +
                                 COALESCE(biomass_net_nominal_capacity, 0) +
                                 COALESCE(hydro_net_nominal_capacity, 0);



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
    nnc_per_capita                     NUMERIC(20, 2),
    nnc_per_capita_rank_within_germany INTEGER,
    nnc_per_capita_rank_within_state   INTEGER,
    nnc_per_capita_rank_within_county  INTEGER
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

DROP TABLE IF EXISTS municipality_keys;
CREATE TABLE municipality_keys
(
    municipality_key VARCHAR(8),
    municipality     VARCHAR(200),
    area             NUMERIC(20, 2),
    population       INTEGER
);

UPDATE current_totals
SET population = (SELECT population
                  FROM municipality_keys
                  WHERE municipality_key = current_totals.municipality_key)
;

UPDATE current_totals
SET population = 0
WHERE population IS NULL;

-- calculate total of all renewable energy sources
UPDATE current_totals
SET total_net_nominal_capacity = COALESCE(pv_net_nominal_capacity, 0) + COALESCE(wind_net_nominal_capacity, 0) +
                                 COALESCE(biomass_net_nominal_capacity, 0) +
                                 COALESCE(hydro_net_nominal_capacity, 0);

-- calculate nnc per capita
UPDATE current_totals
SET nnc_per_capita = total_net_nominal_capacity / population
WHERE population != 0;

-- create ranks on the national level
WITH cte AS (SELECT municipality_key,
                    nnc_per_capita,
                    RANK() OVER (
                        ORDER BY nnc_per_capita DESC
                        ) rank_within_germany
             FROM current_totals
             WHERE nnc_per_capita IS NOT NULL)
UPDATE current_totals
SET nnc_per_capita_rank_within_germany=rank_within_germany
FROM cte
WHERE current_totals.municipality_key = cte.municipality_key;


-- create ranks per state
WITH cte AS (SELECT municipality_key,
                    state,
                    nnc_per_capita,
                    RANK() OVER (
                        PARTITION BY state ORDER BY nnc_per_capita DESC
                        ) rank_within_state
             FROM current_totals
             WHERE nnc_per_capita IS NOT NULL)
UPDATE current_totals
SET nnc_per_capita_rank_within_state=rank_within_state
FROM cte
WHERE current_totals.municipality_key = cte.municipality_key;

-- create ranks per county
WITH cte AS (SELECT municipality_key,
                    state,
                    nnc_per_capita,
                    RANK() OVER (
                        PARTITION BY county ORDER BY nnc_per_capita DESC
                        ) rank_within_county
             FROM current_totals
             WHERE nnc_per_capita IS NOT NULL)
UPDATE current_totals
SET nnc_per_capita_rank_within_county=rank_within_county
FROM cte
WHERE current_totals.municipality_key = cte.municipality_key;
