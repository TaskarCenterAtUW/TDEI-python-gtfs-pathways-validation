FROM python:3.10
WORKDIR /code
# MobilityData's GTFS validator runs on Java (17 or later)
RUN apt-get update \
    && apt-get install -y --no-install-recommends default-jre-headless \
    && rm -rf /var/lib/apt/lists/*
COPY ./scripts/download-gtfs-validator.sh /code/scripts/download-gtfs-validator.sh
RUN /code/scripts/download-gtfs-validator.sh /code/lib
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./src /code/src
EXPOSE 8080
CMD ["uvicorn", "src.main:app", "--reload", "--host", "0.0.0.0", "--port", "8080"]
