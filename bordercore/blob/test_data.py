import logging
import os

import boto3
from botocore.errorfactory import ClientError
import django
from django.conf import settings
from django.db.models import Count, Min, Max, Q
import pytest

from elasticsearch import Elasticsearch

logging.getLogger("elasticsearch").setLevel(logging.ERROR)

django.setup()

from django.contrib.auth.models import User

from accounts.models import SortOrder
from blob.models import Document, MetaData
from collection.models import Collection
from tag.models import Tag

bucket_name = settings.AWS_STORAGE_BUCKET_NAME

s3_client = boto3.client("s3")

blobs_to_skip = [
    "032adf25-92d7-4f26-914c-83e6e3782281",
    "08406fc2-9d57-4bff-9364-8730a8bb2311",
    "0bc6586a-4e8b-4644-b863-374b9fc514fa",
    "19109276-21b1-4fb5-a336-87e248afa89d",
    "50d894af-8dad-44ab-a15e-2435dd8f827a",
    "56ba664e-e918-4598-b198-8e01da064f75",
    "9091c1fe-baca-4c5c-a8b8-b059fc75d50a",
    "95546f46-3842-49d4-93d3-82fad914e3ce",
    "9c461f7e-7a1b-4f44-a312-053184d803c0",
    "b9d3b971-682a-42ba-9db4-6b867edd60eb",
    "d4cb9434-46d6-411b-8062-1421abbcc624",
    "ed124f8d-e5c1-4221-bad4-74b64bac152e",
]


@pytest.fixture()
def es():

    es = Elasticsearch(
        [settings.ELASTICSEARCH_ENDPOINT],
        timeout=120,
        verify_certs=False
    )

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

    found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["total"]["value"]

    assert found == 0, f"{found} books fail this test"


def test_documents_with_dates(es):
    "Assert that all documents have a date"
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

    found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["total"]["value"]

    assert found == 0, f"{found} documents fail this test"


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
    # print(json.dumps(es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]))
    assert found == 0, f"{found} documents fail this test"


def test_books_with_title(es):
    "Assert that all books have a title"
    search_object = {
        "query": {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "must_not": [
                                {
                                    "exists": {
                                        "field": "title"
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

    assert found == 0, f"{found} books fail this test"


def test_books_with_author(es):
    "Assert that all books have at least one author"
    search_object = {
        "query": {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "must_not": [
                                {
                                    "exists": {
                                        "field": "author"
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
    assert found["total"]["value"] == 0, f"{found['total']['value']} books fail this test, uuid={found['hits'][0]['_id']}"


def test_tags_all_lowercase():
    "Assert that all tags are lowercase"
    t = Tag.objects.filter(name__regex=r"[[:upper:]]+")
    assert len(t) == 0, "{} tags fail this test".format(len(t))


def test_tags_no_orphans():
    "Assert that all tags are used by some object"
    t = Tag.objects.filter(Q(todo__isnull=True) &
                           Q(document__isnull=True) &
                           Q(bookmark__isnull=True) &
                           Q(collection__isnull=True) &
                           Q(question__isnull=True) &
                           Q(song__isnull=True) &
                           Q(sortorder__isnull=True) &
                           Q(tagbookmark__isnull=True) &
                           Q(userprofile__isnull=True))
    assert len(t) == 0, "{} tags fail this test; example: name={}".format(len(t), t[0].name)


def test_favorite_tags_sort_order():
    """
    This test checks for three things:

    For every user, min(sort_order) = 1
    For every user, max(sort_order) should equal the total count
    No duplicate sort_order values for each user
    """
    for user in User.objects.all():
        count = SortOrder.objects.filter(user_profile__user=user).count()
        if count > 0:
            assert SortOrder.objects.filter(user_profile__user=user).aggregate(Min("sort_order"))["sort_order__min"] == 1, "Min(sort_order) is not 1 for user={}".format(user)
            assert SortOrder.objects.filter(user_profile__user=user).aggregate(Max("sort_order"))["sort_order__max"] == count, "Max(sort_order) does not equal total count for user={}".format(user)

    q = SortOrder.objects.values("sort_order", "user_profile_id").order_by().annotate(dcount=Count("sort_order")).filter(dcount__gt=1)
    assert len(q) == 0, "Multiple sort_order values found"


# def test_blobs_on_filesystem_exist_in_db():
#     "Assert that all blobs found on the filesystem exist in the database"
#     p = re.compile(settings.MEDIA_ROOT + "/\w\w/(\w{40})")

#     for root, subdirs, files in os.walk(settings.MEDIA_ROOT):
#         matches = p.match(root)
#         if matches:
#             assert Document.objects.filter(sha1sum=matches.group(1)).count() == 1, "blob {} exists on filesystem but not in database".format(matches.group(1))


def test_blobs_in_db_exist_in_elasticsearch(es):
    "Assert that all blobs in the database exist in Elasticsearch"

    blobs = Document.objects.all()

    for b in blobs:
        if str(b.uuid) in blobs_to_skip:
            continue
        search_object = {
            "query": {
                "term": {
                    "uuid.keyword": b.uuid
                }
            },
            "_source": ["uuid"]
        }

        found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["total"]["value"]
        assert found == 1, f"blob found in the database but not in Elasticsearch, uuid={b.uuid}"


def test_images_have_thumbnails():
    "Assert that every image blob has a thumbnail"

    for blob in Document.objects.filter(~Q(file="")):

        if blob.is_image():
            key = "{}/{}/{}/cover.jpg".format(
                settings.MEDIA_ROOT,
                blob.sha1sum[0:2],
                blob.sha1sum,
                blob.file
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
                "must": [
                    {
                        "exists": {
                            "field": "sha1sum"
                        }
                    }
                ]
            }
        },
        "from": 0, "size": 10000,
        "_source": ["filename", "sha1sum", "uuid"]
    }

    found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["hits"]

    for blob in found:
        try:
            key = f"{settings.MEDIA_ROOT}/{blob['_source']['sha1sum'][:2]}/{blob['_source']['sha1sum']}/{blob['_source']['filename']}"
            s3_client.head_object(Bucket=bucket_name, Key=key)
        except ClientError:
            assert False, f"blob {blob['_source']['sha1sum']} exists in Elasticsearch but not in S3"


# def test_solr_blobs_exist_on_filesystem():
#     "Assert that all blobs in Solr exist on the filesystem"
#     solr_args = {"q": "sha1sum:[* TO *]",
#                  "fl": "filepath,sha1sum",
#                  "rows": 2147483647,
#                  "wt": "json"}

#     conn = SolrConnection("http://{}:{}/{}".format(settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
#     response = conn.raw_query(**solr_args)
#     data = json.loads(response.decode("UTF-8"))["response"]
#     for result in data["docs"]:
#         assert os.path.isfile(result.get("filepath", "")) is not False, "blob {} exists in Solr but not on the filesystem".format(result["sha1sum"])


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
        assert Document.objects.filter(uuid=blob["_source"]["uuid"]).count() == 1, f"blob {blob['_source']['uuid']} exists in Elasticsearch but not in database"


# def test_blob_permissions():
#     "Assert that all blobs are owned by www-data and all directories have permissions 775"
#     import os
#     from os import stat
#     from pwd import getpwuid

#     owners = ("celery", "www-data")
#     walk_dir = "/home/media/blobs/"

#     for root, subdirs, files in os.walk(walk_dir):
#         for subdir in subdirs:
#             dir_path = os.path.join(root, subdir)
#             permissions = oct(stat(dir_path).st_mode & 0o777)
#             assert permissions == "0o775", "directory is not 775 {}: {}".format(dir_path, permissions)
#         for filename in files:
#             file_path = os.path.join(root, filename)
#             assert getpwuid(stat(file_path).st_uid).pw_name in owners, "file not owned by {}: {}".format(owners, file_path)


def test_collection_blobs_exists_in_db():
    "Assert that all blobs currently in collections actually exist in the database"
    collections = Collection.objects.filter(blob_list__isnull=False)

    for c in collections:
        for blob in c.blob_list:
            assert Document.objects.filter(pk=blob["id"]).count() > 0, "blob_id {} does not exist in the database".format(blob["id"])


def test_collection_blobs_exists_in_elasticsearch(es):
    "Assert that all blobs currently in collections actually exist in Elasticsearch"

    collections = Collection.objects.filter(blob_list__isnull=False)

    for c in collections:
        for blob_info in c.blob_list:

            blob = Document.objects.get(pk=blob_info["id"])
            if str(blob.uuid) in blobs_to_skip:
                continue

            search_object = {
                "query": {
                    "term": {
                        "uuid.keyword": blob.uuid
                    }
                },
                "_source": ["uuid"]
            }

            found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["total"]["value"]
            assert found == 1, f"blob found in a collection but not in Elasticsearch, uuid={blob.uuid}"


def test_blob_metadata_exists_in_elasticsearch(es):
    "Assert that blob metadata exists in Elasticsearch"

    metadata = MetaData.objects.all()

    for m in metadata:
        if str(m.blob.uuid) in blobs_to_skip:
            continue
        name = m.name.lower()
        if name == "is_book" or name == "":
            continue
        # TODO: Temporary
        if name == "url" or name == "description" or name == "subtitle":
            continue

        search_object = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "uuid.keyword": str(m.blob.uuid)
                            }
                        },
                        {
                            "term": {
                                f"{name}.keyword": m.value
                            }
                        }
                    ]
                }
            },
            "from": 0, "size": 10000,
            "_source": ["filename", "sha1sum", "uuid"]
        }

        found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["total"]["value"]
        assert found == 1, f"metadata for blob uuid={m.blob.uuid} does not exist in Elasticsearch, {m.name}:{m.value}"


def test_elasticsearch_search(es):
    "Assert that a simple Elasticsearch search works"

    search_object = {
        "query": {
            "multi_match": {
                "query": "carl sagan",
                "fields": ["contents", "title"]
            }
        },
        "_source": ["uuid"]
    }

    found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["total"]["value"]
    assert found >= 1, f"Simple Elasticsearch fails"


def test_blob_tags_match_elasticsearch(es):
    "Assert that all blob tags match those found in Elasticsearch"

    blobs = Document.objects.filter(tags__isnull=False)

    for b in blobs:

        if str(b.uuid) in blobs_to_skip:
            continue

        tag_query = [
            {
                "term": {
                    "tags.keyword": x.name
                }
            }
            for x in b.tags.all()
        ]

        search_object = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "uuid.keyword": b.uuid
                            }
                        },
                        tag_query
                    ]
                }
            },
            "from": 0, "size": 10000,
            "_source": ["uuid"]
        }

        found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["total"]["value"]

        assert found == 1, f"blob uuid={b.uuid} has tags which don't match those found in Elasticsearch"


def test_blobs_have_proper_metadata():
    "Assert that all blobs have proper S3 metadata"

    s3 = boto3.resource("s3")

    for blob in Document.objects.filter(~Q(file="")):

        if blob.uuid in blobs_to_skip:
            continue
        obj = s3.Object(bucket_name=bucket_name, key=blob.get_s3_key())
        try:
            obj.metadata["file-modified"]
        except KeyError:
            assert False, f"blob uuid={blob.uuid} has no 'file-modified' S3 metadata"

        if blob.is_image():
            try:
                obj.metadata["image-height"]
            except KeyError:
                assert False, f"image uuid={blob.uuid} has no 'image-height' S3 metadata"


def test_all_notes_exist_in_elasticsearch(es):
    "Assert that all notes exist in Elasticsearch"

    notes = Document.objects.filter(is_note=True)

    for note in notes:

        search_object = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "uuid.keyword": note.uuid
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
