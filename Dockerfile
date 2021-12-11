FROM python:3.10.1-slim

RUN apt update
RUN apt -y install build-essential
RUN pip install uwsgi requests build

ADD . /data
RUN cd /data/ && python3 -m build && pip install /data/dist/*.whl

WORKDIR /data/tests
ENTRYPOINT uwsgi --ini uwsgi.ini
