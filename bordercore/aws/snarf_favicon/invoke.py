import json
import sys

import boto3


client = boto3.client("lambda")


if len(sys.argv) == 2:
    url = sys.argv[1]
else:
    raise Exception("Please provide a url")

payload = {
    "url": url,
    "parse_domain": True
}

response = client.invoke(
    ClientContext="MyApp",
    FunctionName="SnarfFavicon",
    InvocationType="Event",
    LogType="Tail",
    Payload=json.dumps(payload)
)

print(response)
