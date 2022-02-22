#!/bin/bash

BUCKET=bordercore-blobs
TEMPLATE_FILE=packaged.yaml
SAM=~/.local/bin/sam
EFS_DIR=/mnt/efs
BLOB_DIR=/mnt/efs/blobs
EFS_ACCESS_POINT=fsap-034583ce1fe88d1b4

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
     --parameter-overrides ParameterKey=DRFTokenParameter,ParameterValue=${DRF_TOKEN} \ ParameterKey=ElasticsearchEndpointParameter,ParameterValue=${ELASTICSEARCH_ENDPOINT} \
     ParameterKey=EFSMountPointParameter,ParameterValue=$EFS_DIR \
     ParameterKey=BlobDirParameter,ParameterValue=$BLOB_DIR \
     ParameterKey=EFSAccessPointParameter,ParameterValue=$EFS_ACCESS_POINT
