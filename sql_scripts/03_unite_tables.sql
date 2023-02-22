/*
These commands transform the data to only contain the needed values and prepare it for being treated like timeseries data.
1. Create new table energy_units.
2. Copy necessary columns from solar_extended, wind_extended, biomass_extended and hydro_extended.
3. Delete rows that have not been approved (grid_operator_status)
4. Prepare data for easier time-series-analysis by duplicating rows that are no longer active and set the value to negative and the new timestamp
5. Set min date to 2000-01-01 as this project is only interested in the development from 2000 on.
*/

DROP TABLE IF EXISTS energy_units;


CREATE TABLE energy_units
(
    unit_nr                      VARCHAR(50),
    grid_operator_status         VARCHAR(3),
    municipality_key             VARCHAR(8),
    municipality                 VARCHAR(200),
    county                       VARCHAR(200),
    state                        VARCHAR(200),
    zip_code                     VARCHAR(6),
    start_up_date                DATE,
    close_down_date              DATE,
    date                         DATE,
    pv_net_nominal_capacity      NUMERIC(20, 2),
    wind_net_nominal_capacity    NUMERIC(20, 2),
    biomass_net_nominal_capacity NUMERIC(20, 2),
    hydro_net_nominal_capacity   NUMERIC(20, 2),
    storage_net_nominal_capacity NUMERIC(20, 2)
);

INSERT INTO energy_units (unit_nr, grid_operator_status, municipality_key, municipality, county,
                          state, zip_code, start_up_date,
                          close_down_date, date, hydro_net_nominal_capacity)
SELECT einheitmastrnummer,
       netzbetreiberpruefungstatus,
       gemeindeschluessel,
       gemeinde,
       landkreis,
       bundesland,
       postleitzahl,
       inbetriebnahmedatum,
       datumendgueltigestilllegung,
       inbetriebnahmedatum,
       nettonennleistung
FROM hydro_extended;

INSERT INTO energy_units (unit_nr, grid_operator_status, municipality_key, municipality, county,
                          state, zip_code, start_up_date,
                          close_down_date, date, wind_net_nominal_capacity)
SELECT einheitmastrnummer,
       netzbetreiberpruefungstatus,
       gemeindeschluessel,
       gemeinde,
       landkreis,
       bundesland,
       postleitzahl,
       inbetriebnahmedatum,
       datumendgueltigestilllegung,
       inbetriebnahmedatum,
       nettonennleistung
FROM wind_extended;

INSERT INTO energy_units (unit_nr, grid_operator_status, municipality_key, municipality, county,
                          state, zip_code, start_up_date,
                          close_down_date, date, biomass_net_nominal_capacity)
SELECT einheitmastrnummer,
       netzbetreiberpruefungstatus,
       gemeindeschluessel,
       gemeinde,
       landkreis,
       bundesland,
       postleitzahl,
       inbetriebnahmedatum,
       datumendgueltigestilllegung,
       inbetriebnahmedatum,
       nettonennleistung
FROM biomass_extended;

INSERT INTO energy_units (unit_nr, grid_operator_status, municipality_key, municipality, county,
                          state, zip_code, start_up_date,
                          close_down_date, date, pv_net_nominal_capacity)
SELECT einheitmastrnummer,
       netzbetreiberpruefungstatus,
       gemeindeschluessel,
       gemeinde,
       landkreis,
       bundesland,
       postleitzahl,
       inbetriebnahmedatum,
       datumendgueltigestilllegung,
       inbetriebnahmedatum,
       nettonennleistung
FROM solar_extended;

INSERT INTO energy_units (unit_nr, grid_operator_status, municipality_key, municipality, county,
                          state, zip_code, start_up_date,
                          close_down_date, date, storage_net_nominal_capacity)
SELECT einheitmastrnummer,
       netzbetreiberpruefungstatus,
       gemeindeschluessel,
       gemeinde,
       landkreis,
       bundesland,
       postleitzahl,
       inbetriebnahmedatum,
       datumendgueltigestilllegung,
       inbetriebnahmedatum,
       nettonennleistung
FROM storage_extended;

-- Drop units that are not approved or disapproved
DELETE
FROM energy_units
WHERE grid_operator_status = '0';

ALTER TABLE energy_units
    DROP COLUMN grid_operator_status;


-- Duplicate rows with units not longer being active and make their values negative
INSERT INTO energy_units (unit_nr, municipality_key, municipality, county,
                          state, zip_code, start_up_date,
                          close_down_date, date, pv_net_nominal_capacity, wind_net_nominal_capacity,
                          biomass_net_nominal_capacity, hydro_net_nominal_capacity, storage_net_nominal_capacity)
SELECT unit_nr,
       municipality_key,
       municipality,
       county,
       state,
       zip_code,
       start_up_date,
       close_down_date,
       date,
       -pv_net_nominal_capacity,
       -wind_net_nominal_capacity,
       -biomass_net_nominal_capacity,
       -hydro_net_nominal_capacity,
       -storage_net_nominal_capacity
FROM energy_units
WHERE close_down_date is not null;

-- set time to the minimum of 2000-01-01 as this is where we start displaying data
UPDATE energy_units
SET date = '2000-01-01'
WHERE date < '2000-01-01';

ALTER TABLE energy_units ALTER COLUMN date SET NOT NULL;
ALTER TABLE energy_units ADD COLUMN id SERIAL PRIMARY KEY;

DROP TABLE IF EXISTS monthly_timeline;

CREATE TABLE monthly_timeline
    (date, municipality_key, municipality, county, state, zip_code, pv_net_nominal_capacity, wind_net_nominal_capacity,
     biomass_net_nominal_capacity, hydro_net_nominal_capacity, storage_net_nominal_capacity)
AS
SELECT date_trunc('month', date) AS date_monthly,
       municipality_key,
       municipality,
       county,
       state,
       string_agg(DISTINCT zip_code,','),
       sum(pv_net_nominal_capacity),
       sum(wind_net_nominal_capacity),
       sum(biomass_net_nominal_capacity),
       sum(hydro_net_nominal_capacity),
       sum(storage_net_nominal_capacity)
FROM energy_units
GROUP BY date_monthly, municipality_key, municipality, county, state;

-- add indexes for faster searching
CREATE INDEX state_idx ON monthly_timeline (state);
CREATE INDEX county_idx ON monthly_timeline (county);
CREATE INDEX municipality_idx ON monthly_timeline (municipality);
CREATE INDEX municipality_key_idx ON monthly_timeline (municipality_key);

-- add ID column (needed by Django)
ALTER TABLE monthly_timeline
    ADD COLUMN id SERIAL PRIMARY KEY;

DROP TABLE IF EXISTS current_totals;
CREATE TABLE current_totals
(
    id                           SERIAL PRIMARY KEY,
    municipality_key             VARCHAR(8),
    municipality                 VARCHAR(200),
    county                       VARCHAR(200),
    state                        VARCHAR(200),
    zip_code                     TEXT,
    pv_net_nominal_capacity      NUMERIC(20, 2),
    wind_net_nominal_capacity    NUMERIC(20, 2),
    biomass_net_nominal_capacity NUMERIC(20, 2),
    hydro_net_nominal_capacity   NUMERIC(20, 2),
    total_net_nominal_capacity   NUMERIC(20, 2),
    storage_net_nominal_capacity NUMERIC(20, 2),
    population                   INTEGER,
    area                         NUMERIC(20, 2),
    energy_units                 INTEGER
);

INSERT INTO current_totals (municipality_key, municipality, county, state, zip_code, pv_net_nominal_capacity,
                            wind_net_nominal_capacity, biomass_net_nominal_capacity, hydro_net_nominal_capacity,
                            storage_net_nominal_capacity)
SELECT municipality_key,
       municipality,
       county,
       state,
       string_agg(DISTINCT zip_code,','),
       sum(pv_net_nominal_capacity),
       sum(wind_net_nominal_capacity),
       sum(biomass_net_nominal_capacity),
       sum(hydro_net_nominal_capacity),
       sum(storage_net_nominal_capacity)
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

UPDATE current_totals
SET total_net_nominal_capacity = coalesce(pv_net_nominal_capacity, 0) + coalesce(wind_net_nominal_capacity, 0) +
                                 coalesce(biomass_net_nominal_capacity, 0) + coalesce(hydro_net_nominal_capacity, 0);

-- Count energy units per municipality key
WITH subquery AS (
    SELECT municipality_key, COUNT(municipality_key) AS NB_UNITS
    FROM  energy_units
    WHERE close_down_date IS NULL
    GROUP BY municipality_key
)
UPDATE current_totals
SET energy_units = subquery.NB_UNITS
FROM subquery
WHERE current_totals.municipality_key = subquery.municipality_key;




-- remove duplicate zip_code
UPDATE current_totals
set zip_code = array_to_string(array(SELECT DISTINCT unnest(string_to_array(zip_code, ','))), ',');
