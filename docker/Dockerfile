FROM python:3.6-alpine3.7

ADD ../http-server/server.py /

RUN pip install cachetools
RUN pin install logentries
RUN pip install requests

CMD [ "python", "./server.py" ]
