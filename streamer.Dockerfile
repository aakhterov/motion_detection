FROM python:3.10-slim

MAINTAINER Alexander Akhterov "a.ahterov@gmail.com"

COPY src/streamer/requirements.txt /app/src/streamer/
RUN apt-get update && apt-get install -y python3-opencv
RUN pip install --no-cache-dir -r /app/src/streamer/requirements.txt

COPY src/streamer/controller /app/src/streamer/controller
COPY src/streamer/interfaces /app/src/streamer/interfaces
COPY src/streamer/model /app/src/streamer/model
COPY src/streamer/main.py /app/src/streamer/
COPY src/streamer/__init__.py /app/src/streamer/
COPY src/config.py /app/src/
COPY src/__init__.py /app/src/
COPY config.json /app/

RUN mkdir /app/data
WORKDIR /app

EXPOSE 8000

CMD ["fastapi", "dev", "src/streamer/main.py", "--host", "0.0.0.0"]
