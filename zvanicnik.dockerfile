FROM python:3

RUN mkdir -p /opt/src/zvanicnik
WORKDIR /opt/src/zvanicnik

COPY zvanicnik ./

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/zvanicnik"

CMD ["flask", "run"]

