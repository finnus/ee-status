"""Add the indexes and primary keys the data tables should already have.

current_totals, monthly_timeline and energy_units are built outside Django by
sql_scripts/03_unite_tables.sql and are mapped by unmanaged models, so Django
never creates anything for them. The production database was not built by that
script and carries no indexes and no primary keys at all, which leaves every
lookup on the 1.2 million row monthly_timeline as a sequential scan.

The index names deliberately match the ones 03_unite_tables.sql creates, so a
database built by that script already satisfies this migration and a re-import
does not end up with two indexes per column.

Everything is guarded by to_regclass, because the tables do not exist in a
database Django created on its own, such as the test database.
"""

from django.db import migrations

CREATE_INDEXES = """
DO $$
BEGIN
    IF to_regclass('public.monthly_timeline') IS NOT NULL THEN
        CREATE INDEX IF NOT EXISTS state_idx ON monthly_timeline (state);
        CREATE INDEX IF NOT EXISTS county_idx ON monthly_timeline (county);
        CREATE INDEX IF NOT EXISTS municipality_idx ON monthly_timeline (municipality);
        CREATE INDEX IF NOT EXISTS municipality_key_idx
            ON monthly_timeline (municipality_key);
    END IF;

    IF to_regclass('public.current_totals') IS NOT NULL THEN
        CREATE INDEX IF NOT EXISTS totals_state_idx ON current_totals (state);
        CREATE INDEX IF NOT EXISTS totals_county_idx ON current_totals (county);
        CREATE INDEX IF NOT EXISTS totals_municipality_idx
            ON current_totals (municipality);
        CREATE INDEX IF NOT EXISTS totals_municipality_key_idx
            ON current_totals (municipality_key);
    END IF;
END $$;
"""

DROP_INDEXES = """
DROP INDEX IF EXISTS state_idx;
DROP INDEX IF EXISTS county_idx;
DROP INDEX IF EXISTS municipality_idx;
DROP INDEX IF EXISTS municipality_key_idx;
DROP INDEX IF EXISTS totals_state_idx;
DROP INDEX IF EXISTS totals_county_idx;
DROP INDEX IF EXISTS totals_municipality_idx;
DROP INDEX IF EXISTS totals_municipality_key_idx;
"""

# Django's ORM addresses every row of these models by `id`, so the column should
# carry the primary key the import script gives it. Adding one rewrites the
# table's constraint under an ACCESS EXCLUSIVE lock, which on monthly_timeline
# means a pause of a few seconds.
ADD_PRIMARY_KEYS = """
DO $$
DECLARE
    tbl text;
BEGIN
    FOREACH tbl IN ARRAY ARRAY['current_totals', 'monthly_timeline', 'energy_units']
    LOOP
        CONTINUE WHEN to_regclass('public.' || tbl) IS NULL;
        CONTINUE WHEN EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conrelid = to_regclass('public.' || tbl) AND contype = 'p'
        );
        EXECUTE format('ALTER TABLE %I ADD PRIMARY KEY (id)', tbl);
    END LOOP;
END $$;
"""

DROP_PRIMARY_KEYS = """
DO $$
DECLARE
    tbl text;
    con text;
BEGIN
    FOREACH tbl IN ARRAY ARRAY['current_totals', 'monthly_timeline', 'energy_units']
    LOOP
        CONTINUE WHEN to_regclass('public.' || tbl) IS NULL;
        SELECT conname INTO con FROM pg_constraint
        WHERE conrelid = to_regclass('public.' || tbl) AND contype = 'p';
        IF con IS NOT NULL THEN
            EXECUTE format('ALTER TABLE %I DROP CONSTRAINT %I', tbl, con);
        END IF;
    END LOOP;
END $$;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("mastr_data", "0002_alter_monthlytimeline_table"),
    ]

    operations = [
        migrations.RunSQL(sql=CREATE_INDEXES, reverse_sql=DROP_INDEXES),
        migrations.RunSQL(sql=ADD_PRIMARY_KEYS, reverse_sql=DROP_PRIMARY_KEYS),
    ]
