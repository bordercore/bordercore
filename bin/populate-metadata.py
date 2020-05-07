# Sample script showing how to add metadata to all S3 objects which match a regex.
#  In this case, add the key-value pair ("cover-image", "Yes") to all objects
#  which have the filename "cover-small.jpg"

import re

import boto3
from boto3 import client

bucket_name = "bordercore-blobs"


s3_client = client("s3")
s3_resource = boto3.resource("s3")

paginator = s3_client.get_paginator('list_objects')
page_iterator = paginator.paginate(Bucket=bucket_name)

for page in page_iterator:

    for key in page["Contents"]:

        # blobs/f7/f7a63e40b2c4cc095dab6279caf4a6959e542e2f/cover
        p = re.compile(r"^blobs/\w{2}/\w{40}/cover-small.jpg")
        if p.match(str(key["Key"])):

            print(key["Key"])
            response = s3_client.head_object(Bucket=bucket_name, Key=key["Key"])

            if response["Metadata"].get("cover-image", None) == "Yes":
                print(" metadata already found. Skipping")
            else:
                print(" Adding metadata")
                s3_object = s3_resource.Object(bucket_name, key["Key"])
                s3_object.metadata.update({"cover-image": "Yes"})
                s3_object.copy_from(
                    CopySource={"Bucket": bucket_name, "Key": key["Key"]},
                    Metadata=s3_object.metadata, MetadataDirective="REPLACE")
