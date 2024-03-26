FROM python:3.10.12-slim

RUN mkdir app-congreso

WORKDIR /app-congreso

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y gcc default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app-congreso/requirements.txt
RUN pip3 install -r requirements.txt

COPY app.py /app-congreso/app.py

CMD [ "gunicorn", "--workers=5", "--threads=1", "-b 0.0.0.0:8000", "app:server"]

