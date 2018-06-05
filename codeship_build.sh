#!/usr/bin/env bash

eval $(aws ecr get-login --no-include-email --region us-east-1)

versionString=$(eval git describe)
version=${versionString##*/}

docker build -t otm-spec-server .
docker tag otm-spec-server 675074472457.dkr.ecr.us-east-1.amazonaws.com/otm-spec-server:latest
docker tag otm-spec-server 675074472457.dkr.ecr.us-east-1.amazonaws.com/otm-spec-server:$version
docker push 675074472457.dkr.ecr.us-east-1.amazonaws.com/otm-spec-server:latest
docker push 675074472457.dkr.ecr.us-east-1.amazonaws.com/otm-spec-server:$version