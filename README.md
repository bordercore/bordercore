Getting started.

Clone the repo:

```
    git clone https://github.com/bordercore/django.git
```

Build the Elasticsearch docker image:

```
cd bordercore/config/elasticsearch
docker --network=host build -t elasticsearch-with-attachment .
```
Run a container:

```
docker run --rm -p 9201:9200 -p 9301:9300 -e "discovery.type=single-node" elasticsearch-with-attachment:latest
```

Wait for Elasticsearch to spin up, then in another window add the
pipeline attachment and field mappings:

```
cd bordercore/config/elasticsearch
curl -XPUT http://localhost:9201/_ingest/pipeline/attachment -H 'Content-Type: application/json' -d @ingest_pipeline.json
export MAPPINGS="./bordercore/config/elasticsearch/mappings.json"
curl -XPUT http://localhost:9201/bordercore_test -H "Content-Type: application/json" -d @$MAPPINGS
```

Finally, run the functional tests:
```
cd bordercore
make test_functional
```

It would be nice to find a way to automatically add the pipeline
attachment and field mappings when building the image. I'm not sure
how to do this.
