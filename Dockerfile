FROM python:3.6-alpine3.7

COPY http-server/server.py /

RUN pip install cachetools
RUN pip install logentries
RUN pip install requests

CMD [ "python", "./server.py" ]
