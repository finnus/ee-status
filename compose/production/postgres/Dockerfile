# PostGIS rather than plain postgres: the imported MaStR tables carry `geometry`
# columns (current_totals.geom, energy_units.geolocation), so the server needs the
# postgis extension to hold them. The Django app itself does not use GeoDjango,
# so no GDAL/GEOS is needed in the app image.
FROM docker.io/postgis/postgis:17-3.5

COPY ./compose/production/postgres/maintenance /usr/local/bin/maintenance
RUN chmod +x /usr/local/bin/maintenance/*
RUN mv /usr/local/bin/maintenance/* /usr/local/bin \
    && rmdir /usr/local/bin/maintenance
