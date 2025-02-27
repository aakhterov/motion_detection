FROM python:3.10-slim

MAINTAINER Alexander Akhterov "a.ahterov@gmail.com"

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src/detector /app/src/detector
COPY config.json /app

RUN mkdir /app/data
WORKDIR /app

CMD python /app/src/detector/main.py
