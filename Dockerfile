FROM python:3.6-alpine3.7

COPY http-server/server.py /

RUN pip install cachetools
RUN pip install logentries
RUN pip install requests
RUN pip install datadog
RUN pip install semver

RUN mkdir -p "lib/redoc-2.0.0-alpha.23"

RUN wget "https://cdn.jsdelivr.net/npm/redoc@2.0.0-alpha.23/bundles/redoc.standalone.js" -P "lib/redoc-2.0.0-alpha.23/"
RUN wget "https://cdn.jsdelivr.net/npm/redoc@2.0.0-alpha.23/bundles/redoc.standalone.js.map" -P "lib/redoc-2.0.0-alpha.23/"

EXPOSE 9000

CMD [ "python", "./server.py" ]
