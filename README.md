# OpenTripModel.org OTM 4

This is the source code repository of the OTM 4 API Reference Documentation of
[OpenTripModel.org](https://opentripmodel.org). General information on
OpenTripModel can be found at
[opentripmodel.org](https://opentripmodel.org). The OTM 4
reference documentation that is generated out of this source code repository is
published at [developer.opentripmodel.org](https://developer.opentripmodel.org).

## What is OpenTripModel?
OpenTripModel is a simple, free, lightweight and easy-to-use data model, used to
exchange real-time logistic trip data on the web. It provides users a
standarised digital vocabulary to describe and exchange the information
**before**, **during** and **after** transport operations within a logistics
supply chain. Read more on the
[OpenTripModel.org website](https://opentripmodel.org).

## What is OTM 4?
OpenTripModel version 4 is an older version of OTM that became deprecated once 
[OTM5](https://otm5.opentripmodel.org/) was formally released in 2020. If you are
a new user of OTM, we strongly advise you use OTM5. We keep the OTM 4 reference
documentation around only for users who need to keep supporting existing OTM 4
connections.

## What is in this repository?
This repository contains the OpenAPI specification for the OpenTripModel API in
YAML format, as well as some tooling to automatically publish the documentation
Read the following sections in this README for more information about the tooling 
and scripts.

The repository also includes a simple Python HTTP-server, that serves all files
needed to render the documentation. This server can be found in 
[http-server/server.py](http-server/server.py).

The server will serve a HTML-file, that includes
[Redoc](https://github.com/Rebilly/ReDoc) to render the `swagger.yaml`
in a more human readable fashion.

### How to generate a distribution
The documentation server is distributed as a [Docker](https://www.docker.com/what-docker)
container. To create a container from sources, you should install Docker on your
machine. Then run 

```bash
docker build -t otm-spec-server .
```

to build the container. Then the container can be started as follows:

```bash
docker run -p 9000:9000 -e "GITHUB_TOKEN=GitHub Token here" -e "LOG_LEVEL=DEBUG" otm-spec-server 
``` 

### Running the server locally
The HTTP server can also be run locally, without the need to build a Docker 
container. To do so, you'll need to install Python 3.6 (or higher) on your local
machine. Also, you'll need to install some dependencies:

```bash
pip install cachetools
pip install logentries
pip install requests
pip install datadog
pip install semver
```

You will also need to add the redoc js library. From the repository's root directory:
```bash
mkdir -p "lib/redoc"
wget "https://cdn.jsdelivr.net/npm/redoc@2.0.0-alpha.41/bundles/redoc.standalone.js" -P "lib/redoc"
wget "https://cdn.jsdelivr.net/npm/redoc@2.0.0-alpha.41/bundles/redoc.standalone.js.map" -P "lib/redoc"
```

After that, you can start the server:

```bash
cd http-server
python ./server.py
```

The server expects some environment variables to be set:

* `GITHUB_TOKEN`: a GitHub token to access the GitHub repository via the 
  GitHub API. This is needed because the different versions of the 
  specification are loaded from GitHub.
* `LOGENTRIES_TOKEN`: Token to publish application logs to 
  [Logentries](https://logentries.com/). If not set, logs will only be
  written to the console.
* `DATADOG_API_KEY`: Token to publish metrics to 
  [Datadog](https://www.datadoghq.com/). If not set, no metrics will be sent.
* `ENVIRONMENT`: the environment that will be reported to 
  [Datadog](https://www.datadoghq.com/), to be able to distinguish metrics
  from different environments. Only necessary if `DATADOG_API_KEY` is set.
* `LOCAL_HTML_FILE`: Boolean, indicating if the `index.html` file should
  be served from the local file system (`true`) or from GitHub (`false`).
  If omitted, the file is served from GitHub.
  
  This variable cannot be used for the Docker container, because it does not contain the HTML file.
  
  Note: Older versions of the `index.html` are no longer compatible with the current redoc setup.
  To see older versions of the spec locally, either set this variable to `false` or install the
  old redoc versions as described in the Dockerfile.
* `LOCAL_SWAGGER_FILE`: Boolean, indicating if the `swagger.yaml` file should
  be served from the local file system (`true`) or from GitHub (`false`).
  If omitted, the file is served from GitHub.
  
  This variable cannot be used for the Docker container, because it does not contain the Swagger file.
  

## Licence
<a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-sa/4.0/88x31.png" /></a><br />All OpenTripModel documentation is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0 International License</a>.
