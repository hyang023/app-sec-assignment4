FROM ubuntu:18.04

RUN apt-get update -y && \
    apt-get install -y python3.4 && \
    apt-get install -y python3-pip

COPY ./requirements.txt /requirements.txt

WORKDIR /

RUN pip3 install -r requirements.txt

COPY . /

ENV FLASK_APP=app.py
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

ENTRYPOINT export FLASK_APP=app.py && python3 -m flask run --host=0.0.0.0

#CMD flask run
