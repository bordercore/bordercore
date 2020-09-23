#!/bin/bash

BUCKET=bordercore-blobs
TEMPLATE_FILE=packaged.yaml
SAM=~/.local/bin/sam

# We copy the dependencies rather than use symlinks because
#  symlinks don't work inside a "--use-container" Docker image
cp ../../lib/util.py ./lib/
cp ../../blob/elasticsearch_indexer.py ./lib/

$SAM build --use-container &&

$SAM package \
     --s3-bucket $BUCKET \
     --output-template-file packaged.yaml &&

$SAM deploy \
     --template-file $TEMPLATE_FILE \
     --stack-name IndexBlobStack \
     --capabilities CAPABILITY_IAM \
     --parameter-overrides ParameterKey=DatabaseEndpointParameter,ParameterValue=${DATABASE_ENDPOINT} \
     ParameterKey=DatabasePasswordParameter,ParameterValue=${DATABASE_PASSWORD} \
     ParameterKey=ElasticsearchEndpointParameter,ParameterValue=${ELASTICSEARCH_ENDPOINT}
