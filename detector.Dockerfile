FROM python:3.10-slim

MAINTAINER Alexander Akhterov "a.ahterov@gmail.com"

COPY src/detector/requirements.txt /app/src/detector/
RUN apt-get update && apt-get install -y python3-opencv
RUN pip install --no-cache-dir -r /app/src/detector/requirements.txt

COPY src/detector/interface /app/src/detector/interface
COPY src/detector/model /app/src/detector/model
COPY src/detector/main.py /app/src/detector/
COPY src/detector/__init__.py /app/src/detector/
COPY src/config.py /app/src/
COPY src/__init__.py /app/src/
COPY config.json /app/

RUN mkdir /app/data
ENV PYTHONPATH "${PYTHONPATH}:/app"
WORKDIR /app

CMD ["python", "src/detector/main.py"]