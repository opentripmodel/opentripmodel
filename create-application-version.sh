#!/usr/bin/env bash
VERSION="$1"
DATE="$2"

#Place the zip for the app in the correct s3 bucket.
resultName=${VERSION}-${DATE}-opentripmodel-server.zip
mv opentripmodel.zip ${resultName}
aws s3 cp ${resultName} s3://simacan-jenkins-apps/builds/opentripmodel-server/
aws elasticbeanstalk create-application-version \
  --application-name opentripmodel-server-stub \
  --version-label "${VERSION}-${DATE}-opentripmodel-server"  \
  --description "${CI_MESSAGE:0:200}" \
  --source-bundle S3Bucket="simacan-jenkins-apps",S3Key="builds/opentripmodel-server/${resultName}" \
  --no-auto-create-application
