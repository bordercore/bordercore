import logging
import re
from pathlib import Path

import boto3
import pytest
from botocore.errorfactory import ClientError
from elasticsearch import Elasticsearch

import django
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Max, Min, Q

from lib.util import get_missing_blob_ids, is_image

logging.getLogger("elasticsearch").setLevel(logging.ERROR)

pytestmark = pytest.mark.data_quality

django.setup()

from accounts.models import SortOrder, SortOrderNote  # isort:skip
from django.contrib.auth.models import User  # isort:skip
from blob.models import BLOBS_NOT_TO_INDEX, Blob, ILLEGAL_FILENAMES, MetaData   # isort:skip
from collection.models import Collection  # isort:skip
from drill.models import Question  # isort:skip
from tag.models import Tag  # isort:skip


BLOB_DIR = "/home/media"

bucket_name = settings.AWS_STORAGE_BUCKET_NAME


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

    found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]

    assert found["total"]["value"] == 0, f"{found['total']['value']} documents fail this test, uuid={found['hits'][0]['_id']}"


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


def test_books_with_contents(es):
    "Assert that all books have contents"
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
        if match["_source"]["filename"].endswith("pdf") and match["_id"] not in BLOBS_NOT_TO_INDEX:
            assert False, f"Book fails this test, uuid={match['_id']}"


def test_tags_all_lowercase():
    "Assert that all tags are lowercase"
    t = Tag.objects.filter(name__regex=r"[[:upper:]]+")
    assert len(t) == 0, "{} tags fail this test".format(len(t))


def test_tags_no_orphans():
    "Assert that all tags are used by some object"
    t = Tag.objects.filter(Q(todo__isnull=True) &
                           Q(blob__isnull=True) &
                           Q(bookmark__isnull=True) &
                           Q(collection__isnull=True) &
                           Q(question__isnull=True) &
                           Q(song__isnull=True) &
                           Q(sortorder__isnull=True) &
                           Q(tagbookmark__isnull=True) &
                           Q(userprofile__isnull=True))
    assert len(t) == 0, "{} tags fail this test; example: name={}".format(len(t), t.first().name)


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


def test_favorite_notes_sort_order():
    """
    This test checks for three things:

    For every user, min(sort_order) = 1
    For every user, max(sort_order) should equal the total count
    No duplicate sort_order values for each user
    """
    for user in User.objects.all():
        count = SortOrderNote.objects.filter(user_profile__user=user).count()
        if count > 0:
            assert SortOrderNote.objects.filter(user_profile__user=user).aggregate(Min("sort_order"))["sort_order__min"] == 1, "Min(sort_order) is not 1 for user={}".format(user)
            assert SortOrderNote.objects.filter(user_profile__user=user).aggregate(Max("sort_order"))["sort_order__max"] == count, "Max(sort_order) does not equal total count for user={}".format(user)

    q = SortOrderNote.objects.values("sort_order", "user_profile_id").order_by().annotate(dcount=Count("sort_order")).filter(dcount__gt=1)
    assert len(q) == 0, "Multiple sort_order values found"


def test_blobs_in_db_exist_in_elasticsearch(es):
    "Assert that all blobs in the database exist in Elasticsearch"

    blobs = Blob.objects.exclude(uuid__in=BLOBS_NOT_TO_INDEX).only("uuid")
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

    unique_sha1sums = {}

    paginator = s3_resource.meta.client.get_paginator("list_objects")
    page_iterator = paginator.paginate(Bucket=bucket_name)

    for page in page_iterator:
        for key in page["Contents"]:
            m = re.search(r"^blobs/\w{2}/(\w{40})/", str(key["Key"]))
            if m:
                unique_sha1sums[m.group(1)] = True

    for key in unique_sha1sums.keys():
        try:
            Blob.objects.get(sha1sum=key)
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist(f"Blob found in S3 but not in DB: {key}")


def test_images_have_thumbnails():
    "Assert that every image blob has a thumbnail"

    # Create the client here rather than at the top of the module
    #  to avoid interfering with moto mocks in other tests.
    s3_client = boto3.client("s3")

    for blob in Blob.objects.filter(~Q(file="")):

        if is_image(blob.file):
            key = "{}/{}/{}/cover.jpg".format(
                settings.MEDIA_ROOT,
                blob.sha1sum[0:2],
                blob.sha1sum,
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

    s3_resource = boto3.resource("s3")

    unique_sha1sums = {}

    paginator = s3_resource.meta.client.get_paginator("list_objects")
    page_iterator = paginator.paginate(Bucket=bucket_name)

    for page in page_iterator:
        for key in page["Contents"]:
            m = re.search(r"^blobs/\w{2}/(\w{40})/", str(key["Key"]))
            if m:
                unique_sha1sums[m.group(1)] = True

    for blob in found:
        if not blob["_source"]["sha1sum"] in unique_sha1sums:
            assert False, f"blob {blob['_source']['sha1sum']} exists in Elasticsearch but not in S3"


@pytest.mark.wumpus
def test_blobs_in_s3_exist_on_filesystem():
    "Assert that all blobs in S3 exist on the filesystem"

    s3_resource = boto3.resource("s3")

    paginator = s3_resource.meta.client.get_paginator("list_objects")
    page_iterator = paginator.paginate(Bucket=bucket_name)

    for page in page_iterator:
        for key in page["Contents"]:
            m = re.search(r"^(blobs/\w{2}/\w{40})/(.+)", str(key["Key"]))
            if m:
                file_path = f"{BLOB_DIR}/{key['Key']}"
                filename = m.group(2)
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
            m = re.search(r"^(blobs/\w{2}/\w{40})/(.+)", str(key["Key"]))
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


# def test_blob_permissions():
#     "Assert that all blobs are owned by www-data and all directories have permissions 775"
#     import os
#     from os import stat
#     from pwd import getpwuid

#     owners = ("celery", "www-data")
#     walk_dir = "/home/media/blobs/"
#     TODO: Use pathlib instead of os.path
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
            assert Blob.objects.filter(pk=blob["id"]).count() > 0, "blob_id {} does not exist in the database".format(blob["id"])


def test_collection_blobs_exists_in_elasticsearch(es):
    "Assert that all blobs currently in collections actually exist in Elasticsearch"

    collections = Collection.objects.filter(blob_list__isnull=False)

    for c in collections:
        for blob_info in c.blob_list:

            blob = Blob.objects.get(pk=blob_info["id"])
            if str(blob.uuid) in BLOBS_NOT_TO_INDEX:
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

    metadata = MetaData.objects.exclude(blob__uuid__in=BLOBS_NOT_TO_INDEX)

    for m in metadata:
        name = m.name.lower()
        if name == "is_book" or name == "":
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
                            "match": {
                                f"{name}": {
                                    "query": m.value,
                                    "operator": "and"
                                }
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

    blobs = Blob.objects.filter(tags__isnull=False).exclude(uuid__in=BLOBS_NOT_TO_INDEX)

    for b in blobs:

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

    for blob in Blob.objects.filter(~Q(file="")):

        obj = s3.Object(bucket_name=bucket_name, key=blob.get_s3_key())
        try:
            obj.metadata["file-modified"]
        except KeyError:
            assert False, f"blob uuid={blob.uuid} has no 'file-modified' S3 metadata"

        if is_image(blob.file):
            try:
                obj.metadata["image-height"]
            except KeyError:
                assert False, f"image uuid={blob.uuid} has no 'image-height' S3 metadata"


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
    assert found["total"]["value"] == 0, f"{found['total']['value']} blobs fail this test; example: uuid={found['hits'][0]['_source']['uuid']}"


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


def test_questions_no_tags():
    "Assert that all drill questions have at least one tag"
    t = Question.objects.filter(Q(tags__isnull=True))
    assert len(t) == 0, f"{len(t)} questions have no tags; example: {t.first().question}"
