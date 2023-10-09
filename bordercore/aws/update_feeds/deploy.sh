#!/bin/bash

IMAGE_REPO=192218769908.dkr.ecr.us-east-1.amazonaws.com/update-feeds-lambda
TEMPLATE_FILE=packaged.yaml
SAM=~/.local/bin/sam

$SAM build --use-container &&

$SAM package \
     --image-repository $IMAGE_REPO \
     --output-template-file packaged.yaml &&

$SAM deploy \
     --template-file $TEMPLATE_FILE \
     --stack-name UpdateFeedsStack \
     --capabilities CAPABILITY_IAM \
     --parameter-overrides ParameterKey=DRFTokenParameter,ParameterValue=${DRF_TOKEN} \
     --image-repository $IMAGE_REPO
