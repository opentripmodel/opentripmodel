FROM python:3.6-alpine3.7

RUN mkdir /usr/src/app
WORKDIR /usr/src/app

RUN apk update && \
    apk upgrade && \
    apk add git

COPY . .
