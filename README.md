# OpenTripModel.org

This is the source code repository of the API Reference Documentation of
[OpenTripModel.org](https://opentripmodel.org). General information on
OpenTripModel can be found at
[opentripmodel.org](https://opentripmodel.orghttps://opentripmodel.org). The
reference documentation that is generated out of this source code repository is
published at [developer.opentripmodel.org](https://developer.opentripmodel.org).

## What is OpenTripModel?
OpenTripModel is a simple, free, lightweight and easy-to-use data model, used to
exchange real-time logistic trip data on the web. It provides users a
standarised digital vocabulary to describe and exchange the information
**before**, **during** and **after** transport operations within a logistics
supply chain. Read more on the
[OpenTripModel.org website](https://opentripmodel.org).

## What is in this repository?
This repository contains the OpenAPI specification for the OpenTripModel API in
YAML format, as well as some tooling to automatically publish the documentation
and to generate a simple stub server for testing purposes. Read the following
sections in this README for more information about the tooling and scripts.

### How to generate a distribution
The `build.sh` script can build a distribution on any system that has a bash
shell. The resulting `opentripmodel.zip` file is a distribution that can be
uploaded to AWS Elastic Beanstalk. This distribution will publish a
[ReDoc](https://github.com/Rebilly/ReDoc)-rendered view on the API specification
in the root of the server. The distribution also contains a Node.js-based stub
server that will be running at the path `/api/`. This is what is currently
published and running on the
[developer.opentripmodel.org](https://developer.opentripmodel.org) domain.

To create the distribution, open up a shell and type
```
./build.sh
```

### How to deploy a new version on Beanstalk

Either

- Upload the generated `opentripmodel.zip` file to AWS Beanstalk via the AWS web
  interface.

or

- Use the AWS command line tools to create an application version and publish a
  distribution. You can refer to `codeship-ci.sh` and
  `create-application-version.sh` to see what commands are involved.

### How to run the server locally
The generated server code is placed in a `dist` directory by the build script.
So to run locally, run the build script first, as described above. Then run:

```
cd dist
npm start
```

Now you can view the API in several ways:

* To view the [Redoc](https://github.com/Rebilly/ReDoc) interface:
  ```
  open http://localhost:8080/
  ```
  The Redoc interface is the only one that displays the API in the right way,
  since it is the only UI that supports the `discriminator` feature of
  SwaggerSpec, that is used extensively in the API. However, for now, Redoc
  doesn't have a "try it" button
  [yet](https://github.com/Rebilly/ReDoc/issues/53), therefore, you can use the
  Swagger UI too.

* To view the Swagger UI interface:
  ```
  open http://localhost:8080/docs
  ```
  Swagger UI doesn't display the API correctly, since it doesn't support the
  `discriminator` feature of SwaggerSpec.

* To try the API with the stub server, fire HTTP requests to
  `https://localhost:8080/api/`.
