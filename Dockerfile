FROM python:3.10
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple tdei-gtfs-csv-validator==0.0.31
COPY ./src /code/src
EXPOSE 8080
CMD ["uvicorn", "src.main:app", "--reload", "--host", "0.0.0.0", "--port", "8080"]