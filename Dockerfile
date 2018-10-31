FROM python:3.6-alpine3.7

COPY http-server/server.py /

RUN pip install cachetools && \
    pip install logentries && \
    pip install requests && \
    pip install datadog && \
    pip install semver

RUN mkdir -p "lib/redoc-2.0.0-alpha.38" && \
    wget "https://cdn.jsdelivr.net/npm/redoc@2.0.0-alpha.38/bundles/redoc.standalone.js" -P "lib/redoc-2.0.0-alpha.38/" && \
    wget "https://cdn.jsdelivr.net/npm/redoc@2.0.0-alpha.38/bundles/redoc.standalone.js.map" -P "lib/redoc-2.0.0-alpha.38/"

EXPOSE 9000

CMD [ "python", "./server.py" ]
