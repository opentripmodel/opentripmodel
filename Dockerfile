FROM python:3.7-alpine3.9

COPY http-server/server.py /

RUN pip install cachetools && \
    pip install logentries && \
    pip install requests && \
    pip install datadog && \
    pip install semver

# Because the server retrieves older OTM version specs from Github and because those were, at one point, hardcoded on versioned
# directories, these two old redoc versions are required for backwards compatibility.
RUN mkdir -p "lib/redoc-2.0.0-alpha.23" && \
    wget "https://cdn.jsdelivr.net/npm/redoc@2.0.0-alpha.23/bundles/redoc.standalone.js" -P "lib/redoc-2.0.0-alpha.23/" && \
    wget "https://cdn.jsdelivr.net/npm/redoc@2.0.0-alpha.23/bundles/redoc.standalone.js.map" -P "lib/redoc-2.0.0-alpha.23/"

RUN mkdir -p "lib/redoc-2.0.0-alpha.38" && \
    wget "https://cdn.jsdelivr.net/npm/redoc@2.0.0-alpha.38/bundles/redoc.standalone.js" -P "lib/redoc-2.0.0-alpha.38/" && \
    wget "https://cdn.jsdelivr.net/npm/redoc@2.0.0-alpha.38/bundles/redoc.standalone.js.map" -P "lib/redoc-2.0.0-alpha.38/"

RUN mkdir -p "lib/redoc" && \
    wget "https://cdn.jsdelivr.net/npm/redoc@2.0.0-rc.11/bundles/redoc.standalone.js" -P "lib/redoc/" && \
    wget "https://cdn.jsdelivr.net/npm/redoc@2.0.0-rc.11/bundles/redoc.standalone.js.map" -P "lib/redoc/"

EXPOSE 9000

CMD [ "python", "./server.py" ]
