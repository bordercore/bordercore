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
from django.core.cache import cache
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.urls import reverse
from django.utils import timezone

from blob.models import Blob, MetaData
from lib.util import get_elasticsearch_connection, is_image, is_pdf, is_video


def get_recent_blobs(user, limit=10, skip_content=False):
    """
    Return an annotated list of the most recently created blobs,
    along with counts of their doctypes.
    """

    if "recent_blobs" in cache:
        return cache.get("recent_blobs")

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
        "_source": ["created_date", "size", "uuid", "name"]
    }

    es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT, timeout=5)

    results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

    doctypes = defaultdict(int)
    doctypes["all"] = len(results["hits"]["hits"])

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

        if blob.content and not skip_content:
            props["content"] = blob.content[:10000]
            props["content_size"] = humanize.naturalsize(len(blob.content))

        if "size" in match["_source"]:
            props["content_size"] = humanize.naturalsize(match["_source"]["size"])

        if is_image(blob.file) or is_pdf(blob.file) or is_video(blob.file):
            props["cover_url"] = blob.get_cover_url(size="large")
            props["cover_url_small"] = blob.get_cover_url(size="small")

        returned_blob_list.append(props)

        doctypes[blob.doctype] += 1

    cache.set("recent_blobs", (returned_blob_list, doctypes))

    return returned_blob_list, doctypes


def import_blob(user, url):

    parsed_url = urlparse(url)

    # We want the domain part of the hostname (eg bordercore.com instead of www.bordercore.com)
    domain = ".".join(parsed_url.netloc.split(".")[1:])

    if domain == "instagram.com":
        return import_instagram(user, parsed_url)
    elif domain == "nytimes.com":
        return import_newyorktimes(user, url)
    elif domain == "artstation.com":
        return import_artstation(user, parsed_url)
    else:
        raise ValueError(f"Site not supported for importing: <strong>{domain}</strong>")


def parse_shortcode(shortcode):
    """
    If the shortcode was given in the form of a url, extract it.
    """

    patterns = [
        r"^https://www.artstation.com/artwork/([^\/]+)/*",
        r"^https://www.instagram.com/\w+/([^\/]+)/*",
        r"^([\w\d]+)$"
    ]

    # url = "https://www.instagram.com/p/CPLicD6K1uv/?utm_source=ig_web_copy_link"
    # url = "https://www.instagram.com/tv/CWbejF6DD9B/?utm_source=ig_web_copy_link"
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
    For example, if given '2021-08-15 23:40:56', return '2021-08-15'
    """
    patterns = [r"^(\d\d\d\d-\d\d-\d\d)", r"^(\d\d\d\d-\d\d-\d\d)"]

    for p in patterns:
        matches = re.compile(p).match(str(date))
        if matches:
            return matches.group(1)

    return date


def import_instagram(user, parsed_url):

    if not user.userprofile.instagram_credentials:
        raise ValueError("Please provide your Instagram credentials in <a href='" + reverse('accounts:prefs') + "'>preferences</a>.")

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
        else:
            raise Exception(f"{type(e)}: {e}")

    short_code = parse_shortcode(parsed_url.geturl())

    try:
        post = Post.from_shortcode(L.context, short_code)
    except Exception as e:
        if str(e).find("Fetching Post metadata failed") != -1:
            raise ValueError("Instagram post not found.")
        else:
            raise Exception(e)

    o = urlparse(post.url)
    base_name, ext = os.path.splitext(Path(o.path).name)
    temp_file = NamedTemporaryFile(delete=True)

    L.download_pic(temp_file.name, post.url, post.date_utc)

    # Instaloader adds a file extension to the file path you give
    #  it, whether you want that or not. So I need to rename the
    #  resulting file to match the temp file generated by
    #  NamedTemporaryFile.
    os.rename(f"{temp_file.name}{ext}", temp_file.name)

    date = parse_date(post.date)

    user = User.objects.get(username=user.username)
    blob = Blob(
        user=user,
        name=post.caption,
        date=date,
        sha1sum=get_sha1sum(temp_file.name)
    )
    blob.file_modified = int(os.path.getmtime(temp_file.name))
    blob.save()

    myfile = File(open(temp_file.name, "rb"))
    filename = f"{base_name}{ext}"
    blob.file.save(filename, myfile)

    url = f"https://instagram.com/p/{post.shortcode}/"
    artist_name = post.owner_profile.full_name

    MetaData.objects.create(user=user, name="Url", value=url, blob=blob)
    MetaData.objects.create(user=user, name="Artist", value=artist_name, blob=blob)

    blob.index_blob()

    return blob


def import_artstation(user, parsed_url):

    short_code = parse_shortcode(parsed_url.geturl())
    url = f"https://www.artstation.com/projects/{short_code}.json"
    result = requests.get(url)

    if not result.ok:
        raise ValueError(f"Error importing image: {result.reason}")

    result = result.json()

    date = parse_date(result["created_at"])

    user = User.objects.get(username=user.username)
    filename = os.path.basename(urlparse(result["assets"][0]["image_url"]).path)

    opener = urllib.request.build_opener()
    opener.addheaders = [("User-agent", "Bordercore/1.0")]
    urllib.request.install_opener(opener)

    temp_file = NamedTemporaryFile(delete=True)

    urllib.request.urlretrieve(result["assets"][0]["image_url"], temp_file.name)

    blob = Blob(
        user=user,
        name=result["title"],
        date=date,
        sha1sum=get_sha1sum(temp_file.name)
    )
    blob.file_modified = int(os.path.getmtime(str(temp_file.name)))
    blob.save()

    myfile = File(open(temp_file.name, "rb"))
    blob.file.save(filename, myfile)

    url = result["permalink"]
    artist_name = result["user"]["full_name"]

    MetaData.objects.create(user=user, name="Url", value=url, blob=blob)
    MetaData.objects.create(user=user, name="Artist", value=artist_name, blob=blob)

    blob.index_blob()

    return blob


def get_authors(author_list):

    return_list = []

    for author in author_list:
        return_list.append(f"{author['firstname']} {author['lastname']}")

    return return_list


def import_newyorktimes(user, url):

    api_key = user.userprofile.nytimes_api_key
    if not api_key:
        raise ValueError("Please provide your NYTimes API key in <a href='" + reverse('accounts:prefs') + "'>preferences</a>.")

    # Remove any extraneous search-args from the url
    url = url.split("?")[0]

    url = f"https://api.nytimes.com/svc/search/v2/articlesearch.json?api-key={api_key}&fq=web_url:(\"{url}\")"
    r = requests.get(url)
    result = r.json()

    if result["status"] == "ERROR":
        raise ValueError(f"There was an error retrieving the article: {result['errors']}")

    matches = result["response"]["docs"]

    if len(matches) > 1:
        raise ValueError("Error: found more than one article matching that url")

    if len(matches) == 0:
        raise ValueError("Error: no articles found matching that url")

    date = datetime.datetime.strptime(matches[0]["pub_date"], "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d")

    user = User.objects.get(username=user.username)
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

    return blob
