![Bordercore Logo](/bordercore/static/img/bordercore-title.png)

---

*Bordercore* is a "Second Brain" personal knowledge base platform, designed to organize your digital life. Imagine a digital sanctuary where all your vital information converges -- notes whispering insights, PDFs sharing knowledge, bookmarks guiding your web exploration, flashcards sparking memory, and todos orchestrating your day. It supports:

- Notes
- PDFs
- Bookmarks
- Todo Lists
- Flashcards
- Music
- Workouts
- RSS Feeds

The platform is built on Django, relies on AWS Lambda for various asyncronous tasks and uses Elasticsearch for search.

Virtually every object in the system can be tagged.

You can search by keyword, tag, or embedding (semantic search).

# Tests

Be sure the following environment variables are set:

```bash
export BORDERCORE_HOME=$INSTALL_DIR/bordercore
export PYTHONPATH=$INSTALL_DIR:$INSTALL_DIR/bordercore
export DJANGO_SETTINGS_MODULE=config.settings.prod
```

To run all unit tests:

```bash
cd $INSTALL_DIR/bordercore
make test_unit
```

To run all functional tests:

```bash
cd $INSTALL_DIR/bordercore
make test_functional
```

To run all data quality tests:

```bash
cd $INSTALL_DIR/bordercore
make test_data
```

## Setup

An instance of Elasticsearch running inside Docker is used during testing. All objects are indexed in Elasticsearch during a test just like production.

To build the image:

```bash
cd $INSTALL_DIR/bordercore/config/elasticsearch
docker build -t elasticsearch-with-attachment .
```

To run a container based on this image:

```bash
docker run --detach --rm -p 9201:9200 -p 9301:9300 -e "discovery.type=single-node" elasticsearch-with-attachment:latest
```

Then add the pipeline attachment and field mappings:

```bash
cd $INSTALL_DIR/bordercore/config/elasticsearch
curl -XPUT http://localhost:9201/_ingest/pipeline/attachment -H 'Content-Type: application/json' -d @ingest_pipeline.json

MAPPINGS=$HOME/dev/django/bordercore/config/elasticsearch/mappings.json
curl -XPUT http://localhost:9201/bordercore_test -H "Content-Type: application/json" -d @$MAPPINGS
```

If you need to delete the `bordercore_test` instance and start fresh, run this:

```bash
cd $INSTALL_DIR/bordercore/
make reset_elasticsearch
```

Elasticsearch is installed in the `/usr/share/elasticsearch` directory in the Docker image.
