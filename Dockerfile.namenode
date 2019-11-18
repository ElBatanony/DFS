FROM python:3.7.4

WORKDIR /app

EXPOSE 8800

ADD . .

RUN apt-get update && apt-get install -y --no-install-recommends gettext && apt-get clean && apt install python3 && pip install requests

CMD python3 naming_server.py

