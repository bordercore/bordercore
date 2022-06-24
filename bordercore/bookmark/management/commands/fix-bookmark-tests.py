import re

import boto3
import requests

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.transaction import atomic

from bookmark.tests.test_data import (test_bookmark_thumbnails_in_s3_exist_in_db,
                                      test_bookmarks_in_db_exist_in_elasticsearch,
                                      test_elasticsearch_bookmarks_exist_in_db)
from lib.util import get_elasticsearch_connection

from bookmark.models import Bookmark  # isort:skip


class Command(BaseCommand):
    help = "Fix bookmark data tests"

    def add_arguments(self, parser):
        parser.add_argument(
            "--test",
            help="The test to fix",
        )
        parser.add_argument(
            "--dry-run",
            help="Dry run. Take no action",
            action="store_true"
        )

    @atomic
    def handle(self, *args, test, dry_run, **kwargs):

        if test == "test_bookmarks_in_db_exist_in_elasticsearch":
            self.fix_test_bookmarks_in_db_exist_in_elasticsearch(dry_run)
        elif test == "test_elasticsearch_bookmarks_exist_in_db":
            self.fix_test_elasticsearch_bookmarks_exist_in_db(dry_run)
        elif test == "test_bookmark_thumbnails_in_s3_exist_in_db":
            self.fix_test_bookmark_thumbnails_in_s3_exist_in_db(dry_run)
        else:
            raise ValueError("No valid test specified.")

    def parse_uuids(self, text):

        pattern = re.compile("^uuid:(.*)")

        uuids = []

        for line in text.split("\n"):
            matches = pattern.match(line)
            if matches:
                uuids.append(matches.group(1))

        return uuids

    def fix_test_bookmarks_in_db_exist_in_elasticsearch(self, dry_run):

        es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)

        try:
            test_bookmarks_in_db_exist_in_elasticsearch(es)
            print("Nothing to fix")
        except AssertionError as error:
            for uuid in self.parse_uuids(str(error)):
                print(f"{uuid} Indexing bookmark in elasticsearch")
                if not dry_run:
                    b = Bookmark.objects.get(uuid=uuid)
                    b.index_bookmark()

    def fix_test_elasticsearch_bookmarks_exist_in_db(self, dry_run):

        es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)

        try:
            test_elasticsearch_bookmarks_exist_in_db(es)
            print("Nothing to fix")
        except AssertionError as error:
            for uuid in self.parse_uuids(str(error)):
                # bookmark_info = get_bookmark_info(uuid)
                print(f"{uuid} Deleting bookmark in elasticsearch")
                if not dry_run:
                    result = requests.post(f"http://{settings.ELASTICSEARCH_ENDPOINT}:9200/bordercore/_delete_by_query?q=uuid:{uuid}")
                    if result.status_code != 200:
                        print(result.response)

    def fix_test_bookmark_thumbnails_in_s3_exist_in_db(self, dry_run):

        try:
            test_bookmark_thumbnails_in_s3_exist_in_db()
            print("Nothing to fix")
        except AssertionError as error:

            s3 = boto3.resource("s3")
            my_bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

            for uuid in self.parse_uuids(str(error)):
                print(f"{uuid} Deleting bookmark thumbnail in S3")
                if not dry_run:
                    for fn in my_bucket.objects.filter(Prefix=f"bookmarks/{uuid}"):
                        print(f"  Deleting {fn}")
                        fn.delete()
