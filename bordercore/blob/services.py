import datetime
import hashlib
import os
import re
import urllib.request
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

import humanize
import instaloader
import requests
from instaloader import Post

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from django.urls import reverse
from django.utils import timezone

from blob.models import Blob, MetaData
from lib.util import get_elasticsearch_connection, is_image, is_pdf, is_video


def get_recent_blobs(user, limit=10):
    """
    Return an annotated list of the most recently created blobs,
    along with counts of their doctypes.
    """

    search_object = {
        "query": {
            "bool": {
                "must": [
                    {
                        "term": {
                            "user_id": user.id
                        }
                    },
                    {
                        "bool": {
                            "should": [
                                {
                                    "term": {
                                        "doctype": "blob"
                                    }
                                },
                                {
                                    "term": {
                                        "doctype": "document"
                                    }
                                },
                                {
                                    "term": {
                                        "doctype": "book"
                                    }
                                },
                            ]
                        }
                    },
                ]
            }
        },
        "sort": {"created_date": {"order": "desc"}},
        "from": 0, "size": limit,
        "_source": ["created_date", "size", "uuid"]
    }

    es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)

    results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

    doctypes = defaultdict(int)

    # Prefetch all matched blobs from the database in one query, rather
    #  than using a separate query for each one in the loop below.
    uuid_list = [x["_source"]["uuid"] for x in results["hits"]["hits"]]
    blob_list = Blob.objects.filter(uuid__in=uuid_list).prefetch_related("tags", "metadata")

    returned_blob_list = []

    for match in results["hits"]["hits"]:

        try:
            blob = next(x for x in blob_list if str(x.uuid) == match["_source"]["uuid"])
        except StopIteration:
            # Handle a race condition in which a blob has just been deleted by the user
            #  but the corresponding document in Elasticsearch is still in the
            #  process of being removed.
            continue

        delta = timezone.now() - blob.modified

        props = {
            "name": blob.name,
            "tags": blob.get_tags(),
            "url": reverse("blob:detail", kwargs={"uuid": blob.uuid}),
            "delta_days": delta.days,
            "uuid": blob.uuid,
            "doctype": blob.doctype,
        }

        if blob.content:
            props["content"] = blob.content[:10000]
            props["content_size"] = humanize.naturalsize(len(blob.content))

        if "size" in match["_source"]:
            props["content_size"] = humanize.naturalsize(match["_source"]["size"])

        if is_image(blob.file) or is_pdf(blob.file) or is_video(blob.file):
            props["cover_url"] = blob.get_cover_url(size="large")

        returned_blob_list.append(props)

        doctypes[blob.doctype] += 1
        doctypes["all"] = len(results["hits"]["hits"])

    return returned_blob_list, doctypes


def import_blob(user, url):

    parsed_url = urlparse(url)

    # We want the domain part of the hostname (eg bordercore.com instead of www.bordercore.com)
    domain = ".".join(parsed_url.netloc.split(".")[1:])

    if domain == "instagram.com":
        return import_instagram(user, parsed_url)
    elif domain == "newyorktimes.com":
        return import_newyorktimes(user, parsed_url)
    elif domain == "artstation.com":
        return import_artstation(user, parsed_url)
    else:
        raise ValueError(f"Site not supported for importing: <strong>{domain}</strong>")


def parse_shortcode(shortcode):
    """
    If the shortcode was given in the form of a url, extract it.
    """

    patterns = [
        r"^https://www.artstation.com/artwork/([^\/]*)/*",
        r"^https://www.instagram.com/p/([^\/]*)/*",
        r"^([\w\d]+)$"
    ]

    # url = "https://www.instagram.com/p/CPLicD6K1uv/?utm_source=ig_web_copy_link"
    # url = "https://www.artstation.com/artwork/CPLicD6K1uv/"
    # url = "CPLicD6K1uv"

    for pattern in patterns:
        match = re.compile(pattern).match(shortcode)
        if match:
            return match.group(1)

    # If we got this far, we couldn't parse the shortcode
    raise ValueError(f"Can't parse shortcode from {shortcode}")


def get_sha1sum(filename):

    BUF_SIZE = 65536

    sha1 = hashlib.sha1()

    with open(filename, "rb") as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)

    return sha1.hexdigest()


def parse_date(date):
    """
    Return the date without the time portion.
    For example, if given '2021-08-15', return '2021-08-15 23:40:56'
    """
    patterns = [r"^(\d\d\d\d-\d\d-\d\d)", r"^(\d\d\d\d-\d\d-\d\d)"]

    for p in patterns:
        matches = re.compile(p).match(str(date))
        if matches:
            return matches.group(1)

    return date


def import_instagram(user, parsed_url):

    if not user.userprofile.instagram_credentials:
        raise ValueError("Please provide your Instagram credentials in  <a href='" + reverse('accounts:prefs') + "'>preferences</a>.")

    L = instaloader.Instaloader(download_videos=True)

    try:
        L.login(
            user.userprofile.instagram_credentials["username"],
            user.userprofile.instagram_credentials["password"]
        )
    except Exception as e:
        if str(e).find("Wrong password") != -1:
            raise ValueError("Login error. Please check your Instagram password in <a href='" + reverse('accounts:prefs') + "'>preferences</a>.")
        elif str(e).find("does not exist") != -1:
            raise ValueError("Login error. Please check your Instagram username in <a href='" + reverse('accounts:prefs') + "'>preferences</a>.")

    short_code = parse_shortcode(parsed_url.geturl())

    try:
        post = Post.from_shortcode(L.context, short_code)
    except Exception as e:
        if str(e).find("Fetching Post metadata failed") != -1:
            raise ValueError("Instagram post not found.")

    # Remove the extension from the image filename, because for
    #  some reason instaloader already adds it after downloading
    o = urlparse(post.url)
    filename = os.path.splitext(Path(o.path).name)[0]

    L.download_pic(filename, post.url, post.date_utc)

    date = parse_date(post.date)

    filename = os.path.basename(urlparse(post.url).path)

    myfile = File(open(filename, "rb"))

    user = User.objects.get(username="jerrell")
    blob = Blob(
        user=user,
        name=post.caption,
        date=date,
        sha1sum=get_sha1sum(filename)
    )
    blob.file_modified = int(os.path.getmtime(str(filename)))
    blob.save()
    blob.file.save(filename, myfile)

    url = f"https://instagram.com/p/{post.shortcode}/"
    artist_name = post.owner_profile.full_name

    MetaData.objects.create(user=user, name="Url", value=url, blob=blob)
    MetaData.objects.create(user=user, name="Artist", value=artist_name, blob=blob)

    os.remove(filename)

    blob.index_blob()

    return blob.uuid


def import_artstation(user, parsed_url):

    short_code = parse_shortcode(parsed_url.geturl())
    url = f"https://www.artstation.com/projects/{short_code}.json"
    result = requests.get(url)

    if not result.ok:
        raise ValueError(f"Error importing image: {result.reason}")

    result = result.json()

    date = parse_date(result["created_at"])

    user = User.objects.get(username="jerrell")

    filename = os.path.basename(urlparse(result["assets"][0]["image_url"]).path)

    opener = urllib.request.build_opener()
    opener.addheaders = [("User-agent", "Bordercore/1.0")]
    urllib.request.install_opener(opener)

    urllib.request.urlretrieve(result["assets"][0]["image_url"], filename)

    blob = Blob(
        user=user,
        name=result["title"],
        date=date,
        sha1sum=get_sha1sum(filename)
    )
    blob.file_modified = int(os.path.getmtime(str(filename)))
    blob.save()

    myfile = File(open(filename, "rb"))
    blob.file.save(filename, myfile)

    url = result["permalink"]
    artist_name = result["user"]["full_name"]

    MetaData.objects.create(user=user, name="Url", value=url, blob=blob)
    MetaData.objects.create(user=user, name="Artist", value=artist_name, blob=blob)

    os.remove(filename)

    blob.index_blob()

    return blob.uuid


def get_authors(author_list):

    return_list = []

    for author in author_list:
        return_list.append(f"{author['firstname']} {author['lastname']}")

    return return_list


def import_newyorktimes(user, title):

    t = datetime.datetime.now()
    month = t.strftime("%m")
    if month.startswith("0"):
        month = month[1:]

    t = datetime.datetime.now()
    year = t.strftime("%Y")

    # TODO: Add this to prefs
    API_KEY = ""

    url = f"https://api.nytimes.com/svc/archive/v1/{year}/{month}.json?api-key={API_KEY}"
    r = requests.get(url)
    result = r.json()

    matches = []

    for foo in result["response"]["docs"]:
        if title.lower() in foo["headline"]["main"].lower():
            matches.append(foo)

    if len(matches) > 1:
        print("Error: found more than one article matching that title")
        for article in matches:
            print(article["headline"]["main"])
        raise ValueError()

    if len(matches) == 0:
        print("Error: no articles found matching that title")
        raise ValueError()

    print(matches[0])

    date = datetime.datetime.strptime(matches[0]["pub_date"], "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d")

    user = User.objects.get(username="jerrell")
    blob = Blob(
        user=user,
        name=matches[0]["headline"]["main"],
        date=date
    )
    blob.save()

    url = matches[0]["web_url"]
    MetaData.objects.create(user=user, name="Url", value=url, blob=blob)

    subtitle = matches[0]["abstract"]
    MetaData.objects.create(user=user, name="Subtitle", value=subtitle, blob=blob)

    author_list = get_authors(matches[0]["byline"]["person"])
    for author in author_list:
        MetaData.objects.create(user=user, name="Author", value=author, blob=blob)

    blob.index_blob()

    return blob.uuid
