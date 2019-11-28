FROM ubuntu

WORKDIR /app

EXPOSE 8800
EXPOSE 8801

ADD naming_server.py .
ADD storage_server.py .
ADD super_client.py .
ADD helpers.py .
ADD constants_and_codes.py .

RUN apt-get -y update
RUN apt-get -y install python3


