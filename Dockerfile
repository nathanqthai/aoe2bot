FROM python:3.9.9-slim

RUN apt-get -y update && apt-get -y upgrade
RUN apt-get -y install libopus0 libffi-dev libnacl-dev python3 python3-dev ffmpeg

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --upgrade pip && pip3 install --no-cache-dir -r requirements.txt

COPY ./aoe2bot /app/aoe2bot

WORKDIR /app/aoe2bot
ENV PYTHONPATH ${PYTHONPATH}:/app

ENTRYPOINT ["python3", "./main.py"]