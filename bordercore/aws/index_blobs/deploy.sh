#!/bin/bash

IMAGE_REPO=192218769908.dkr.ecr.us-east-1.amazonaws.com/index-blob-lambda
TEMPLATE_FILE=packaged.yaml
SAM=~/.local/bin/sam
EFS_DIR=/mnt/efs
BLOB_DIR=/mnt/efs/blobs
EFS_ACCESS_POINT=fsap-034583ce1fe88d1b4

# cp ../../lib/util.py ./lib/
# cp ../../blob/elasticsearch_indexer.py ./lib/

$SAM build --use-container &&

$SAM package \
     --image-repository $IMAGE_REPO \
     --output-template-file packaged.yaml &&

$SAM deploy \
     --template-file $TEMPLATE_FILE \
     --stack-name IndexBlobStack \
     --capabilities CAPABILITY_IAM \
     --image-repository $IMAGE_REPO \
     --parameter-overrides ParameterKey=DRFTokenParameter,ParameterValue=${DRF_TOKEN} \ ParameterKey=ElasticsearchEndpointParameter,ParameterValue=${ELASTICSEARCH_ENDPOINT} \
     ParameterKey=EFSMountPointParameter,ParameterValue=$EFS_DIR \
     ParameterKey=BlobDirParameter,ParameterValue=$BLOB_DIR \
     ParameterKey=EFSAccessPointParameter,ParameterValue=$EFS_ACCESS_POINT
