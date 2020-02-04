#
# youtube-dl Server Dockerfile
#
# https://github.com/manbearwiz/youtube-dl-server-dockerfile
#

FROM python:alpine

RUN apk add --no-cache \
  ffmpeg \
  tzdata

RUN mkdir -p /usr/src/app/share
WORKDIR /usr/src/app
RUN useradd -ms /bin/bash admin

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

RUN chown -R admin:admin /usr/src/app
RUN chmod 755 /usr/src/app
USER admin

EXPOSE 8080

VOLUME ["/youtube-dl/share"]

CMD [ "python", "-u", "./youtube-dl-server.py" ]
