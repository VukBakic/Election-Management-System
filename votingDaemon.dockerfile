FROM python:3

RUN mkdir -p /opt/src/dameon
WORKDIR /opt/src/dameon

COPY daemon ./
RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/daemon"

CMD [ "python","-u", "./src/application.py" ]


