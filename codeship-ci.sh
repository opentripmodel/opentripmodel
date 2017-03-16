#!/usr/bin/env bash
pip install awscli --upgrade

# Has an argument to deploy or not deploy to an environment
DEPLOY=$1

#The date, version and the dockerfiles dir where the zip will end up will all be passed as arguments to the other shell scripts.
DATE=$(date -u "+%Y-%m-%d_%H-%M-%S")
VERSION=`git describe | sed -e 's/\//_/g'`

#Build the docker file
./build.sh

#Deploy it as a application version
./create-application-version.sh ${VERSION} ${DATE}

#Deploy it to the configured environment 
aws elasticbeanstalk update-environment \
  --application-name opentripmodel-server \
  --environment-name opentripmodel-stub-server \
  --version-label "${VERSION}-${DATE}-opentripmodel-server"
