# Example of how to use DRF to add a blob to Bordercore

import json

import requests

filename = "path/to/file"
api_token = "<api token>"
uuid = "<uuid>"

with open(filename, "r") as file:
    contents = file.read()

data = {
    "content": contents,
    "title": "Elasticsearch Notes",
    "user": 1,
    "tags": [1287],
    "date": "2020-05-07",
    "is_note": True
}

url = "https://www.bordercore.com/api/blobs/{uuid}"

headers = {
    "Authorization": f"Token {api_token}",
    "Content-Type": "application/json"
}

# We use a session so that we can set trust_env = None (see below)
s = requests.Session()

# Set this so that the ~/.netrc file is ignored for authentication
s.trust_env = None

r = s.put(url, data=json.dumps(data), headers=headers)
print(r.status_code)
print(r.text)
