#!/bin/bash

BUCKET=bordercore-blobs
TEMPLATE_FILE=packaged.yaml
SAM=~/.local/bin/sam

# We copy the dependencies rather than use symlinks because
#  symlinks don't work inside a "--use-container" Docker image
cp ../../lib/util.py ./lib/
cp ../../lib/thumbnails.py ./lib/

$SAM build --use-container &&

$SAM package \
     --s3-bucket $BUCKET \
     --output-template-file packaged.yaml &&

$SAM deploy \
     --template-file $TEMPLATE_FILE \
     --stack-name CreateThumbnailStack \
     --capabilities CAPABILITY_IAM
