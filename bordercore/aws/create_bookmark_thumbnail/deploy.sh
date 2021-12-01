#!/bin/bash

BUCKET=bordercore-blobs
TEMPLATE_FILE=packaged.yaml
SAM=~/.local/bin/sam
EFS_DIR=/mnt/efs
EFS_ACCESS_POINT=fsap-034583ce1fe88d1b4
SECURITY_GROUP=sg-bfa013fe
SUBNET_1=subnet-2ff16448
SUBNET_2=subnet-ff3712b5

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
     --stack-name CreateBookmarkThumbnailStack \
     --capabilities CAPABILITY_IAM \
     --parameter-overrides ParameterKey=EFSMountPointParameter,ParameterValue=$EFS_DIR \
     ParameterKey=EFSAccessPointParameter,ParameterValue=$EFS_ACCESS_POINT \
     ParameterKey=SecurityGroupParameter,ParameterValue=$SECURITY_GROUP \
     ParameterKey=Subnet1Parameter,ParameterValue=$SUBNET_1 \
     ParameterKey=Subnet2Parameter,ParameterValue=$SUBNET_2
