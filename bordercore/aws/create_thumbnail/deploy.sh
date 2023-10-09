#!/bin/bash

IMAGE_REPO=192218769908.dkr.ecr.us-east-1.amazonaws.com/create-thumbnail-lambda
TEMPLATE_FILE=packaged.yaml
SAM=~/.local/bin/sam
EFS_DIR=/mnt/efs
EFS_ACCESS_POINT=fsap-034583ce1fe88d1b4
SECURITY_GROUP=sg-bfa013fe
SUBNET_1=subnet-2ff16448
SUBNET_2=subnet-ff3712b5

$SAM build --use-container &&

$SAM package \
     --image-repository $IMAGE_REPO \
     --output-template-file packaged.yaml &&

$SAM deploy \
     --template-file $TEMPLATE_FILE \
     --stack-name CreateThumbnailStack \
     --capabilities CAPABILITY_IAM \
     --image-repository $IMAGE_REPO \
     --parameter-overrides ParameterKey=EFSMountPointParameter,ParameterValue=$EFS_DIR \
     ParameterKey=EFSAccessPointParameter,ParameterValue=$EFS_ACCESS_POINT \
     ParameterKey=SecurityGroupParameter,ParameterValue=$SECURITY_GROUP \
     ParameterKey=Subnet1Parameter,ParameterValue=$SUBNET_1 \
     ParameterKey=Subnet2Parameter,ParameterValue=$SUBNET_2
