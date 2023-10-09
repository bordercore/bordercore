#!/bin/bash

IMAGE_REPO=192218769908.dkr.ecr.us-east-1.amazonaws.com/create-collection-thumbnail-lambda
TEMPLATE_FILE=packaged.yaml
SAM=~/.local/bin/sam
EFS_DIR=/mnt/efs
EFS_ACCESS_POINT=fsap-034583ce1fe88d1b4
MAGICK_TEMPORARY_PATH=/mnt/efs

$SAM build --use-container &&

$SAM package \
     --image-repository $IMAGE_REPO \
     --output-template-file packaged.yaml &&

$SAM deploy \
     --template-file $TEMPLATE_FILE \
     --stack-name CreateCollectionThumbnailStack \
     --capabilities CAPABILITY_IAM \
     --image-repository $IMAGE_REPO \
     --parameter-overrides ParameterKey=DRFTokenParameter,ParameterValue=${DRF_TOKEN} \
     ParameterKey=EFSMountPointParameter,ParameterValue=$EFS_DIR \
     ParameterKey=EFSAccessPointParameter,ParameterValue=$EFS_ACCESS_POINT \
     ParameterKey=MagickTemporaryPathParameter,ParameterValue=$MAGICK_TEMPORARY_PATH
