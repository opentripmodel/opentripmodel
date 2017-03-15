#!/usr/bin/env bash

if [ ! -f ./swagger-codegen-cli.jar ]; then
  echo Downloading Swagger Codegen CLI...
  if [ -z ${ARTIFACTORY_USER} ]; then
    echo "Environment variable ARTIFACTORY_USER is not set, can't download from Artifactory. Exiting.";
    exit 1
  fi
  if [ -z ${ARTIFACTORY_PASSWORD} ]; then
    echo "Environment variable ARTIFACTORY_PASSWORD is not set, can't download from Artifactory. Exiting.";
    exit 1
  fi
  # TODO: When Swagger Codegen 2.2.3 is released, we can use the public build from Maven central, for now 
  #       we need this custom build with the fix for invalid example data in generated code.
  curl --user $ARTIFACTORY_USER:$ARTIFACTORY_PASSWORD https://simacan.jfrog.io/simacan/libs-snapshot-local/io/swagger/swagger-codegen-cli/2.2.3-SNAPSHOT/swagger-codegen-cli-2.2.3-20170214.154712-1.jar -o swagger-codegen-cli.jar
fi

if [ -d "dist" ]; then
  echo Removing old 'dist' directory
  rm -rf ./dist
fi

VERSION=`git describe | sed -e 's/version\///g'`
cat api/swagger.yaml | sed -e "s/{{VERSION}}/${VERSION}/g" > api/swagger_v.yaml

echo Executing Swagger Codegen...
java -jar swagger-codegen-cli.jar generate \
  -i api/swagger_v.yaml \
  -l nodejs-server \
  -t templates \
  -o ./dist

echo Copying additional files to 'dist' directory...
cp -r ./redoc ./dist/
cp -r ./images ./dist/
cp ./beanstalk/Dockerfile ./dist/
cp ./beanstalk/Dockerrun* ./dist/
cp ./beanstalk/.dockerignore ./dist/

echo Creating ZIP-file for deployment to AWS EBS
if [ ! -f ./opentripmodel.zip ]; then
  echo Removing old ZIP-file
  rm opentripmodel.zip
fi

cd dist
zip -r opentripmodel.zip *
cd ..
mv dist/opentripmodel.zip .
