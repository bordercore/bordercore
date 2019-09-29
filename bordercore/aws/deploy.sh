#!/bin/bash

BUCKET=bordercore-blobs
TEMPLATE_FILE=packaged.yaml
SAM=~/.local/bin/sam

$SAM build

$SAM package \
     --s3-bucket $BUCKET \
     --output-template-file packaged.yaml &&

$SAM deploy \
     --template-file $TEMPLATE_FILE \
     --stack-name BordercoreStack \
     --capabilities CAPABILITY_IAM
