#Dockerfile

FROM python:3.10.8-slim-bullseye

ARG BUILD_ENVIRONMENT=production
ARG APP_HOME=/app

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

RUN apt-get update && apt-get install --no-install-recommends -y \
  # dependencies for building Python packages
  build-essential \
  # psycopg2 dependencies
  libpq-dev \
  git \
  # Geospatial dependencies
  binutils libproj-dev gdal-bin \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# Copy your requirements.txt file to the container
COPY ./requirements ${APP_HOME}/requirements

# Install Python dependencies directly from requirements.txt
RUN pip install --no-cache-dir -r ${APP_HOME}/requirements/${BUILD_ENVIRONMENT}.txt

COPY ./ /usr/src/app
COPY ./utility/ /usr/src/utility

EXPOSE 80

CMD sh /usr/src/utility/caprover.sh
