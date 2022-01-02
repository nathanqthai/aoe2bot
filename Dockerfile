FROM python:3.9.9-slim

RUN apt-get -y update && apt-get -y upgrade

RUN apt-get -y install libopus0 libffi-dev libnacl-dev python3 python3-dev

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt && pip install discord.py[voice]

COPY *.py /app/
CMD ["python3", "./main.py"]