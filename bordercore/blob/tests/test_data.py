import logging
import re
from pathlib import Path

import boto3
import pytest
from botocore.errorfactory import ClientError

import django
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Max, Min, Q

from lib.util import (get_elasticsearch_connection, get_missing_blob_ids,
                      get_missing_metadata_ids, is_image)

logging.getLogger("elasticsearch").setLevel(logging.ERROR)

pytestmark = pytest.mark.data_quality

django.setup()

from blob.models import Blob, ILLEGAL_FILENAMES, MetaData, RecentlyViewedBlob   # isort:skip
from drill.models import Question  # isort:skip
from tag.models import Tag  # isort:skip


BLOB_DIR = "/home/media"

bucket_name = settings.AWS_STORAGE_BUCKET_NAME


@pytest.fixture()
def es():

    es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)
    yield es


def test_books_with_tags(es):
    "Assert that all books have at least one tag"
    search_object = {
        "query": {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "must_not": [
                                {
                                    "exists": {
                                        "field": "tags"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "term": {
                            "doctype": "book"
                        }
                    }
                ]
            }
        },
        "from": 0, "size": 10000,
        "_source": ["uuid"]
    }

    found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)['hits']

    assert found['total']['value'] == 0, f"{found}['total']['value'] books found without tags, uuid={found['hits'][0]['_id']}"


def test_documents_and_notes_with_dates(es):
    "Assert that all documents and notes have a date"
    search_object = {
        "query": {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "must_not": [
                                {
                                    "exists": {
                                        "field": "date_unixtime"
                                    }
                                },
                                {
                                    "exists": {
                                        "field": "date"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "bool": {
                            "should": [
                                {
                                    "term": {
                                        "doctype": "document"
                                    }
                                },
                                {
                                    "term": {
                                        "doctype": "note"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        },
        "from": 0, "size": 10000,
        "_source": ["uuid"]
    }

    found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]

    assert found["total"]["value"] == 0, f"{found['total']['value']} documents or notes have no date, uuid={found['hits'][0]['_id']}"


def test_videos_with_durations(es):
    "Assert that all videos have a duration"
    search_object = {
        "query": {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "must_not": [
                                {
                                    "exists": {
                                        "field": "duration"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "wildcard": {
                            "content_type": "**video**"
                        }
                    }
                ]
            }
        },
        "from": 0, "size": 10000,
        "_source": ["uuid"]
    }

    found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]

    assert found["total"]["value"] == 0, f"{found['total']['value']} videos found with no duration, uuid={found['hits'][0]['_id']}"


def test_dates_with_unixtimes(es):
    "Assert that all documents with dates also have a date_unixtime field"
    search_object = {
        "query": {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "must_not": [
                                {
                                    "exists": {
                                        "field": "date_unixtime"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "bool": {
                            "must": [
                                {
                                    "exists": {
                                        "field": "date"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "term": {
                            "doctype": "blob"
                        }
                    }
                ]
            }
        },
        "from": 0, "size": 10000,
        "_source": ["uuid"]
    }

    found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["total"]["value"]
    assert found == 0, f"{found} documents fail this test"


def test_books_with_names(es):
    "Assert that all books have a name"
    search_object = {
        "query": {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "must_not": [
                                {
                                    "exists": {
                                        "field": "name"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "term": {
                            "doctype": "book"
                        }
                    }
                ]
            }
        },
        "from": 0, "size": 10000,
        "_source": ["uuid"]
    }

    found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["total"]["value"]

    assert found == 0, f"{found} books found with no name"


def test_books_with_author(es):
    "Assert that all books have at least one author or editor"
    search_object = {
        "query": {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "must_not": [
                                {
                                    "exists": {
                                        "field": "metadata.author"
                                    }
                                },
                                {
                                    "exists": {
                                        "field": "metadata.editor"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "term": {
                            "doctype": "book"
                        }
                    }
                ]
            }
        },
        "from": 0, "size": 10000,
        "_source": ["uuid"]
    }

    found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]
    assert found["total"]["value"] == 0, f"{found['total']['value']} books found with no author, uuid={found['hits'][0]['_id']}"


def test_books_with_contents(es):
    "Assert that all books have contents"
    blobs_not_indexed = [str(x.uuid) for x in Blob.objects.filter(is_indexed=False).only("uuid")]
    search_object = {
        "query": {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "must_not": [
                                {
                                    "exists": {
                                        "field": "attachment"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "term": {
                            "doctype": "book"
                        }
                    }
                ]
            }
        },
        "from": 0, "size": 10000,
        "_source": ["filename", "uuid"]
    }

    found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]

    for match in found["hits"]:
        if match["_source"]["filename"].endswith("pdf") and match["_id"] not in blobs_not_indexed:
            assert False, f"Book has no content, uuid={match['_id']}"


def test_tags_all_lowercase():
    "Assert that all tags are lowercase"
    t = Tag.objects.filter(name__regex=r"[[:upper:]]+")
    assert len(t) == 0, "{} tags fail this test".format(len(t))


def test_blobs_in_db_exist_in_elasticsearch(es):
    "Assert that all blobs in the database exist in Elasticsearch"

    blobs = Blob.objects.filter(is_indexed=True).only("uuid")
    step_size = 100
    blob_count = blobs.count()

    for batch in range(0, blob_count, step_size):

        # The batch_size will always be equal to "step_size", except probably
        #  the last batch, which will be less.
        batch_size = step_size if blob_count - batch > step_size else blob_count - batch

        query = [
            {
                "term": {
                    "_id": str(x.uuid)
                }
            }
            for x
            in blobs[batch:batch + step_size]
        ]

        search_object = {
            "query": {
                "bool": {
                    "should": query
                }
            },
            "size": batch_size,
            "_source": [""]
        }

        found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

        assert found["hits"]["total"]["value"] == batch_size,\
            "blobs found in the database but not in Elasticsearch: " + get_missing_blob_ids(blobs[batch:batch + step_size], found)


def test_blobs_in_s3_exist_in_db():
    "Assert that all blobs in S3 also exist in the database"

    s3_resource = boto3.resource("s3")

    unique_uuids = {}

    paginator = s3_resource.meta.client.get_paginator("list_objects")
    page_iterator = paginator.paginate(Bucket=bucket_name)

    for page in page_iterator:
        for key in page["Contents"]:
            m = re.search(r"^blobs/(.*?)/", str(key["Key"]))
            if m:
                unique_uuids[m.group(1)] = True

    for key in unique_uuids.keys():
        try:
            Blob.objects.get(uuid=key)
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist(f"Blob found in S3 but not in DB: {key}")


def test_images_have_thumbnails():
    "Assert that every image blob has a thumbnail"

    # Create the client here rather than at the top of the module
    #  to avoid interfering with moto mocks in other tests.
    s3_client = boto3.client("s3")

    for blob in Blob.objects.filter(~Q(file="")):

        if is_image(blob.file):
            key = "{}/{}/cover.jpg".format(
                settings.MEDIA_ROOT,
                blob.uuid,
            )
            try:
                s3_client.head_object(Bucket=bucket_name, Key=key)
            except ClientError:
                assert False, f"image blob {blob.uuid} does not have a thumbnail"


def test_elasticsearch_blobs_exist_in_s3(es):
    "Assert that all blobs in Elasticsearch exist in S3"

    search_object = {
        "query": {
            "bool": {
                "must":
                {
                    "exists": {
                        "field": "sha1sum"
                    }
                },
                "must_not":
                {
                    "term": {
                        "sha1sum": ""
                    }
                }
            }
        },
        "from": 0, "size": 10000,
        "_source": ["filename", "sha1sum", "uuid"]
    }

    found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["hits"]

    s3_resource = boto3.resource("s3")

    unique_uuids = {}

    paginator = s3_resource.meta.client.get_paginator("list_objects")
    page_iterator = paginator.paginate(Bucket=bucket_name)

    for page in page_iterator:
        for key in page["Contents"]:
            m = re.search(r"^blobs/(.*?)/", str(key["Key"]))
            if m:
                unique_uuids[m.group(1)] = True

    for blob in found:
        if not blob["_source"]["uuid"] in unique_uuids:
            assert False, f"blob {blob['_source']['uuid']} exists in Elasticsearch but not in S3"


@pytest.mark.wumpus
def test_blobs_in_s3_exist_on_filesystem():
    "Assert that all blobs in S3 exist on the filesystem"

    s3_resource = boto3.resource("s3")

    paginator = s3_resource.meta.client.get_paginator("list_objects")
    page_iterator = paginator.paginate(Bucket=bucket_name)

    for page in page_iterator:
        for key in page["Contents"]:
            m = re.search(r"^blobs/.*?/(.+)", str(key["Key"]))
            if m:
                file_path = f"{BLOB_DIR}/{key['Key']}"
                filename = m.group(1)
                if not Path(file_path).exists() and filename not in ILLEGAL_FILENAMES:
                    assert False, f"blob {key['Key']} exists in S3 but not on the filesystem"


@pytest.mark.wumpus
def test_blobs_on_filesystem_exist_in_s3():
    "Assert that all blobs on the filesystem exist in S3"

    s3_resource = boto3.resource("s3")

    paginator = s3_resource.meta.client.get_paginator("list_objects")
    page_iterator = paginator.paginate(Bucket=bucket_name)

    blobs = {}

    # Create a hash of all blobs in S3 for later lookup
    for page in page_iterator:
        for key in page["Contents"]:
            m = re.search(r"^blobs/.*?/.+", str(key["Key"]))
            if m:
                file_path = f"{BLOB_DIR}/{key['Key']}"
                blobs[file_path] = True

    for x in Path(f"{BLOB_DIR}/blobs").rglob("*"):
        if x.is_file() and blobs.get(str(x), None) is None and x.name not in ILLEGAL_FILENAMES:
            assert False, f"{x} found on the filesystem but not in S3"


def test_elasticsearch_blobs_exist_in_db(es):
    "Assert that all blobs in Elasticsearch exist in the database"
    search_object = {
        "query": {
            "bool": {
                "should": [
                    {
                        "term": {
                            "doctype": "book"
                        }
                    },
                    {
                        "term": {
                            "doctype": "blob"
                        }
                    },
                    {
                        "term": {
                            "doctype": "document"
                        }
                    }
                ]
            }
        },
        "from": 0, "size": 10000,
        "_source": ["uuid"]
    }

    found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["hits"]

    for blob in found:
        assert Blob.objects.filter(uuid=blob["_source"]["uuid"]).count() == 1, f"blob {blob['_source']['uuid']} exists in Elasticsearch but not in database"


@pytest.mark.wumpus
def test_blob_permissions():
    "Assert that all blobs are owned by jerrell and all directories have permissions 775"
    from os import stat
    from pwd import getpwuid

    owner = "jerrell"
    walk_dir = "/home/media/blobs/"

    for file in Path(walk_dir).glob("**/*"):
        if file.is_dir():
            permissions = oct(stat(file).st_mode & 0o777)
            assert permissions == "0o775", f"Directory is not 775 {file}: {permissions}"
        elif file.is_file():
            assert getpwuid(stat(file).st_uid).pw_name == owner, f"File not owned by {owner}: {file}"


def test_blob_metadata_exists_in_elasticsearch(es):
    "Assert that blob metadata exists in Elasticsearch"

    metadata = MetaData.objects.exclude(Q(blob__is_indexed=False)
                                        | Q(name="is_book")
                                        | Q(name=""))
    step_size = 100
    metadata_count = metadata.count()

    for batch in range(0, metadata_count, step_size):

        # The batch_size will always be equal to "step_size", except probably
        #  the last batch, which will be less.
        batch_size = step_size if metadata_count - batch > step_size else metadata_count - batch

        query = [
            {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "uuid": str(x.blob.uuid)
                            }
                        },
                        {
                            "match": {
                                f"metadata.{x.name.lower()}": {
                                    "query": x.value,
                                    "operator": "and"
                                }
                            }
                        }
                    ]
                }
            }
            for x
            in metadata[batch:batch + step_size]
        ]

        # A list of unique metadata names used in this batch
        names = set([x.name.lower() for x in metadata[batch:batch + step_size]])
        names.add("uuid")

        unique_uuids = set([x.blob.uuid for x in metadata[batch:batch + step_size]])

        search_object = {
            "query": {
                "bool": {
                    "should": query
                }
            },
            "from": 0, "size": batch_size,
            "_source": list(names)
        }
        found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)
        assert found["hits"]["total"]["value"] == len(unique_uuids), \
            "metadata for blobs found in the database but not in Elasticsearch: " + get_missing_metadata_ids(metadata[batch:batch + step_size], found)


def test_elasticsearch_search(es):
    "Assert that a simple Elasticsearch search works"

    search_object = {
        "query": {
            "multi_match": {
                "query": "carl sagan",
                "fields": ["contents", "name"]
            }
        },
        "_source": ["uuid"]
    }

    found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["total"]["value"]
    assert found >= 1, "Simple Elasticsearch fails"


def test_blob_tags_match_elasticsearch(es):
    "Assert that all blob tags match those found in Elasticsearch"

    blobs = Blob.objects.filter(tags__isnull=False).exclude(is_indexed=False).distinct("uuid").order_by("uuid")
    step_size = 100
    blob_count = blobs.count()

    for batch in range(0, blob_count, step_size):

        # The batch_size will always be equal to "step_size", except probably
        #  the last batch, which will be less.
        batch_size = step_size if blob_count - batch > step_size else blob_count - batch

        query = [
            {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "uuid": str(b.uuid)
                            }
                        },
                        *[
                            {
                                "term": {
                                    "tags.keyword": x.name
                                }
                            }
                            for x in b.tags.all()
                        ]
                    ]
                }
            }
            for b
            in blobs[batch:batch + step_size]
        ]

        search_object = {
            "query": {
                "bool": {
                    "should": query
                }
            },
            "from": 0, "size": batch_size,
            "_source": ["uuid"]
        }

        found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

        assert found["hits"]["total"]["value"] == batch_size, \
            "blobs found in the database with tags which don't match those found in Elasticsearch: " + get_missing_blob_ids(blobs[batch:batch + step_size], found)


def test_blobs_have_proper_metadata():
    "Assert that all blobs have proper S3 metadata"

    s3 = boto3.resource("s3")

    for blob in Blob.objects.filter(~Q(file="")):

        obj = s3.Object(bucket_name=bucket_name, key=blob.s3_key)
        try:
            obj.metadata["file-modified"]
        except KeyError:
            assert False, f"blob uuid={blob.uuid} has no 'file-modified' S3 metadata"

        assert obj.metadata["file-modified"] != "None", f"blob uuid={blob.uuid} has 'file-modified' = 'None"

        if obj.content_type == "binary/octet-stream":
            assert False, f"blob uuid={blob.uuid} has no proper 'Content-Type' metadata"


def test_no_empty_blob_metadata():
    "Assert that no blobs have empty metadata"
    m = MetaData.objects.filter(Q(name="") or Q(value=""))
    assert len(m) == 0, f"Empty metadata found: count={len(m)}, uuid={m.first().blob.uuid}"


def test_blobs_have_size_field(es):
    "Assert that all blobs have a size field"
    search_object = {
        "query": {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "must_not": [
                                {
                                    "exists": {
                                        "field": "size"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "term": {
                            "doctype": "blob"
                        }
                    }
                ]
            }
        },
        "from": 0, "size": 10000,
        "_source": ["uuid"]
    }

    found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]
    assert found["total"]["value"] == 0, f"{found['total']['value']} blobs found with no size, uuid={found['hits'][0]['_source']['uuid']}"


def test_all_notes_exist_in_elasticsearch(es):
    "Assert that all notes exist in Elasticsearch"

    notes = Blob.objects.filter(is_note=True)

    for note in notes:

        search_object = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "uuid": note.uuid
                            }
                        },
                        {
                            "term": {
                                "doctype": "note"
                            }
                        }
                    ]
                }
            },
            "_source": ["uuid"]
        }

        found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["total"]["value"]
        assert found == 1, f"note uuid={note.uuid} does not exist in Elasticsearch"


def test_questions_no_tags():
    "Assert that all drill questions have at least one tag"
    t = Question.objects.filter(Q(tags__isnull=True))
    assert len(t) == 0, f"{len(t)} questions have no tags; example: {t.first().question}"


def test_recently_viewed_blob_sort_order():
    """
    This test checks for three things for the RecentlyViewedBlob model

    min(sort_order) = 1
    max(sort_order) should equal the total count
    No duplicate sort_order values
    """

    # Get a list of all distinct users...
    blobs = RecentlyViewedBlob.objects.all().only("blob__user").distinct("blob__user")

    # ...and loop through them, checking for integrity constaint violations
    for blob in blobs:
        count = RecentlyViewedBlob.objects.filter(blob__user=blob.blob.user).count()
        max_sort_order = RecentlyViewedBlob.objects.filter(blob__user=blob.blob.user).aggregate(
            Max("sort_order")
        )
        assert max_sort_order["sort_order__max"] == count, \
            f"Max(sort_order) != total count for user {blob.blob.user} in recently viewed blobs"

        min_sort_order = RecentlyViewedBlob.objects.filter(blob__user=blob.blob.user).aggregate(
            Min("sort_order")
        )
        assert min_sort_order["sort_order__min"] == 1, \
            f"Min(sort_order) != 1 for user {blob.blob.user} in recently viewed blobs"

    duplicates = RecentlyViewedBlob.objects.values(
        "sort_order",
        "blob__user"
    ).order_by().annotate(
        dcount=Count("sort_order")
    ).filter(
        dcount__gt=1
    )

    assert len(duplicates) == 0, f"Multiple sort_order values found in recently viewed blobs: {duplicates[0]}"


def test_no_test_data_in_elasticsearch(es):
    "Assert that there is no test data present, as identified by a '__test__' field"
    search_object = {
        "query": {
            "bool": {
                "must": {
                    "exists": {
                        "field": "__test__"
                    }
                },
            }
        },
        "from": 0, "size": 10000,
        "_source": ["uuid"]
    }

    found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]

    assert found["total"]["value"] == 0, f"{found['total']['value']} documents with test data found, uuid={found['hits'][0]['_id']}"
