import logging
import os

import requests

logging.getLogger().setLevel(logging.INFO)
log = logging.getLogger(__name__)

DRF_TOKEN = os.environ.get("DRF_TOKEN")


def handler(event, context):

    try:

        feed_uuid = event["feed_uuid"]

        headers = {"Authorization": f"Token {DRF_TOKEN}"}
        r = requests.get(f"https://www.bordercore.com/api/feeds/update_feed_list/{feed_uuid}/", headers=headers)
        if r.status_code != 200:
            raise Exception(f"Error: status code: {r.status_code}")

        log.info(f"Updated feed_uuid={feed_uuid}, {r.json()}")

    except Exception as e:
        log.error(f"Exception when updating feed_uuid={feed_uuid}: {e}")

    log.info("Lambda finished")
