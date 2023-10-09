#!/bin/bash

IMAGE_REPO=192218769908.dkr.ecr.us-east-1.amazonaws.com/snarf-favicon-lambda
TEMPLATE_FILE=packaged.yaml
SAM=~/.local/bin/sam

$SAM build --use-container &&

$SAM package \
     --image-repository $IMAGE_REPO \
     --output-template-file packaged.yaml &&

$SAM deploy \
     --template-file $TEMPLATE_FILE \
     --stack-name SnarfFaviconStack \
     --capabilities CAPABILITY_IAM \
     --image-repository $IMAGE_REPO
