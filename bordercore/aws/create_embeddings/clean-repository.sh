# Delete all untagged images in the repository

REPOSITORY_NAME=create-embeddings-lambda

aws ecr describe-images --repository-name ${REPOSITORY_NAME} --query 'imageDetails[?imageTags==`null`].[imageDigest]' --output text | while read line
do
    echo "Deleting image with digest: $line"
    aws ecr batch-delete-image --repository-name ${REPOSITORY_NAME} --image-ids imageDigest=$line
done
