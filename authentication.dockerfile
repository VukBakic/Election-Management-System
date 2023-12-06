FROM python:3

RUN mkdir -p /opt/src/authentication
WORKDIR /opt/src/authentication

COPY authentication ./
RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/authentication"


CMD ["flask", "run"]

