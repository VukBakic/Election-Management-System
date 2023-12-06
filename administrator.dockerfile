FROM python:3

RUN mkdir -p /opt/src/administrator
WORKDIR /opt/src/administrator

COPY administrator ./
RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/administrator"

CMD ["flask", "run"]

