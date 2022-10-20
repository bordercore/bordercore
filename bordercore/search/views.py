import datetime
import json
import math
import re
from urllib.parse import unquote

from elasticsearch import RequestError

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView

from blob.models import Blob
from bookmark.models import Bookmark
from lib.time_utils import get_date_from_pattern, get_relative_date
from lib.util import (get_elasticsearch_connection, get_pagination_range,
                      truncate)
from tag.models import Tag
from tag.services import get_tag_aliases, get_tag_link

from .models import RecentSearch

SEARCH_LIMIT = 1000


def get_creators(matches):
    """
    Return all "creator" related fields
    """

    creators = [
        matches[x][0]
        for x
        in matches.keys()
        if x in ["author", "artist", "photographer"]
    ]

    return ", ".join(creators)


@method_decorator(login_required, name="dispatch")
class SearchListView(ListView):

    template_name = "search/search.html"
    context_object_name = "search_results"
    RESULT_COUNT_PER_PAGE = 10

    def get_paginator(self, page, num_results):

        if num_results == 0:
            return {}

        num_pages = int(math.ceil(num_results / self.RESULT_COUNT_PER_PAGE))
        paginate_by = 2

        paginator = {
            "page_number": page,
            "num_pages": num_pages,
            "total_results": num_results,
            "range": get_pagination_range(
                page,
                num_pages,
                paginate_by
            )
        }

        paginator["has_previous"] = page != 1
        paginator["has_next"] = page != paginator["num_pages"]

        paginator["previous_page_number"] = page - 1
        paginator["next_page_number"] = page + 1

        return paginator

    def get_aggregations(self, context, aggregation):

        aggregations = []
        for x in context["search_results"]["aggregations"][aggregation]["buckets"]:
            aggregations.append({"doctype": x["key"], "count": x["doc_count"]})
        return aggregations

    def get_queryset(self):

        # Store the "sort" field in the user's session
        self.request.session["search_sort_by"] = self.request.GET.get("sort", None)

        search_term = self.request.GET.get("search", None)
        sort_field = self.request.GET.get("sort", "date_unixtime")
        boolean_type = self.request.GET.get("boolean_search_type", "AND")
        doctype = self.request.GET.get("doctype", None)

        if search_term:
            RecentSearch.add(self.request.user, search_term)

        es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)

        offset = (int(self.request.GET.get("page", 1)) - 1) * self.RESULT_COUNT_PER_PAGE

        search_object = {
            "query": {
                "function_score": {
                    "field_value_factor": {
                        "field": "importance",
                        "missing": 1
                    },
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "term": {
                                        "user_id": self.request.user.id
                                    }
                                }
                            ]
                        }
                    }
                }
            },
            "aggs": {
                "Doctype Filter": {
                    "terms": {
                        "field": "doctype",
                        "size": 10,
                    }
                }
            },
            "highlight": {
                "fields": {
                    "attachment.content": {},
                    "contents": {},
                },
                "number_of_fragments": 1,
                "fragment_size": 200,
                "order": "score"
            },
            "sort": {sort_field: {"order": "desc"}},
            "from": offset,
            "size": self.RESULT_COUNT_PER_PAGE,
            "_source": ["artist",
                        "author",
                        "bordercore_id",
                        "date",
                        "date_unixtime",
                        "doctype",
                        "filename",
                        "importance",
                        "last_modified",
                        "name",
                        "question",
                        "sha1sum",
                        "tags",
                        "title",
                        "url",
                        "uuid"]
        }

        # Let subclasses modify the query
        search_object = self.refine_search(search_object)

        if doctype:
            search_object["post_filter"] = {
                "term": {
                    "doctype": doctype
                }
            }

        if search_term:
            search_object["query"]["function_score"]["query"]["bool"]["must"].append(
                {
                    "multi_match": {
                        "type": "phrase" if self.request.GET.get("exact_match", None) in ["Yes"] else "best_fields",
                        "query": search_term,
                        "fields": [
                            "answer",
                            "metadata.*",
                            "attachment.content",
                            "contents",
                            "name",
                            "question",
                            "sha1sum",
                            "title",
                            "uuid"
                        ],
                        "operator": boolean_type,
                    }
                }
            )

        try:
            results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)
        except RequestError as e:
            messages.add_message(self.request, messages.ERROR, f"Request Error: {e.status_code} {e.info['error']}")
            return []

        for index, _ in enumerate(results["hits"]["hits"]):
            match = results["hits"]["hits"][index]

            # Django templates don't support variables with underscores or dots, so
            #  we need to transform a few fields
            match["source"] = match.pop("_source")
            match["score"] = match.pop("_score")
            if "highlight" in match and "attachment.content" in match["highlight"]:
                match["highlight"]["attachment_content"] = match["highlight"].pop("attachment.content")

            # Highlight matched terms using markdown italicized text when searching
            if search_term and "contents" in match["source"]:
                match["source"]["contents"] = match["source"]["contents"].replace(search_term, f"*{search_term}*")

        return results

    def refine_search(self, search_object):
        return search_object

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        if "doctype" in self.request.GET:
            context["doctype_filter"] = self.request.GET["doctype"].split(",")

        if context["search_results"]:

            for match in context["search_results"]["hits"]["hits"]:

                match["source"]["creators"] = get_creators(match["source"])
                match["source"]["date"] = get_date_from_pattern(match["source"].get("date", None))
                match["source"]["last_modified"] = get_relative_date(match["source"]["last_modified"])
                if match["source"]["doctype"] in ["book", "blob"]:
                    match["source"]["cover_url"] = Blob.get_cover_url_static(
                        match["source"]["uuid"],
                        match["source"]["filename"],
                        size="small"
                    )
                # Bookmarks are rendered by a Vue component, which requires json
                if match["source"]["doctype"] == "bookmark":
                    match["json"] = json.dumps(match["source"])
            context["aggregations"] = self.get_aggregations(context, "Doctype Filter")

            page = int(self.request.GET.get("page", 1))

            context["paginator"] = json.dumps(
                self.get_paginator(page, context["search_results"]["hits"]["total"]["value"])
            )

        context["title"] = "Search"
        return context


@method_decorator(login_required, name="dispatch")
class NoteListView(SearchListView):

    template_name = "blob/note_list.html"
    RESULT_COUNT_PER_PAGE = 10

    def refine_search(self, search_object):

        page = int(self.request.GET.get("page", 1))
        search_object["from"] = (page - 1) * self.RESULT_COUNT_PER_PAGE

        search_object["_source"].append("contents")

        search_object["query"]["function_score"]["query"]["bool"]["must"].append(
            {
                "term": {
                    "doctype": "note"
                }
            }
        )

        tagsearch = self.request.GET.get("tagsearch", None)
        if tagsearch:
            search_object["query"]["function_score"]["query"]["bool"]["must"].append(
                {
                    "term": {
                        "tags.keyword": tagsearch
                    }
                }
            )

        return search_object

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        page = int(self.request.GET.get("page", 1))
        context["paginator"] = json.dumps(
            self.get_paginator(page, context["search_results"]["hits"]["total"]["value"])
        )

        if "search" not in self.request.GET:
            context["pinned_notes"] = self.request.user.userprofile.pinned_notes.all().only("name", "uuid").order_by("sortorderusernote__sort_order")

        return context


@method_decorator(login_required, name="dispatch")
class SearchTagDetailView(ListView):

    template_name = "search/tag_detail.html"
    RESULT_COUNT_PER_PAGE = 1000
    context_object_name = "search_results"

    def get_queryset(self):

        taglist = self.kwargs.get("taglist", "").split(",")

        es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)

        # Use the keyword field for an exact match
        tag_query = [
            {
                "term": {
                    "tags.keyword": x
                }
            }
            for x in taglist
        ]

        tag_query.append(
            {
                "term": {
                    "user_id": self.request.user.id
                }
            }
        )

        search_object = {
            "query": {
                "function_score": {
                    "field_value_factor": {
                        "field": "importance",
                        "missing": 1
                    },
                    "query": {
                        "bool": {
                            "must": tag_query
                        }
                    }
                }
            },
            "aggs": {
                "Doctype Filter": {
                    "terms": {
                        "field": "doctype",
                        "size": 10
                    }
                },
                "Tag Filter": {
                    "terms": {
                        "field": "tags.keyword",
                        "size": 20
                    }
                }
            },
            "sort": [
                {"importance": {"order": "desc"}},
                {"last_modified": {"order": "desc"}}
            ],
            "from": 0,
            "size": self.RESULT_COUNT_PER_PAGE,
            "_source": [
                "artist",
                "artist_uuid",
                "author",
                "content_type",
                "contents",
                "date",
                "date_unixtime",
                "doctype",
                "filename",
                "importance",
                "bordercore_id",
                "last_modified",
                "name",
                "question",
                "sha1sum",
                "tags",
                "title",
                "url",
                "uuid"
            ]
        }

        results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)
        return results

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        results = {}
        for match in context["search_results"]["hits"]["hits"]:

            result = {
                "artist": match["_source"].get("artist", ""),
                "artist_uuid": match["_source"].get("artist_uuid", ""),
                "question": truncate(match["_source"].get("question", "")),
                "name": match["_source"].get("name", "No Name"),
                "title": match["_source"].get("title", "No Title"),
                "task": match["_source"].get("name", ""),
                "url": match["_source"].get("url", ""),
                "uuid": match["_source"].get("uuid", ""),
                "creators": get_creators(match["_source"]),
                "contents": match["_source"].get("contents", "")[:200],
                "date": get_date_from_pattern(match["_source"].get("date", None))
            }

            if "tags" in match["_source"]:
                # Only show tags that were not searched for
                result["tags"] = [tag for tag in match["_source"]["tags"]
                                  if tag not in self.kwargs["taglist"]]

            if "sha1sum" in match["_source"]:

                result = {
                    "sha1sum": match["_source"]["sha1sum"],
                    "filename": match["_source"].get("filename", ""),
                    "url": Blob.get_s3_key(
                        match["_source"]["uuid"],
                        match["_source"].get("filename", "")
                    ),
                    "cover_url": Blob.get_cover_url_static(
                        match["_source"].get("uuid", ""),
                        match["_source"].get("filename", ""),
                        size="small"
                    ),
                    **result,
                }

                if "content_type" in match["_source"]:
                    result["content_type"] = Blob.get_content_type(match["_source"]["content_type"])

            results.setdefault(match["_source"]["doctype"], []).append(result)

        context["search_results"]["matches"] = results

        # Now that we've created a version of the result set organized by doc_type, we
        #  don't need the original from Elasticsearch. Delete it to reduce payload size.
        context["object_list"].pop("hits")

        tag_list = self.kwargs.get("taglist", "").split(",")

        # Get a list of tags and their counts, to be displayed
        #  in the "Other tags" dropdown
        context["tag_counts"] = self.get_doc_counts(
            tag_list,
            context["search_results"]["aggregations"]["Tag Filter"]
        )

        # Get a list of doc types and their counts
        context["doctype_counts"] = self.get_doc_counts(
            tag_list,
            context["search_results"]["aggregations"]["Doctype Filter"]
        )

        context["meta_tags"] = [x[0] for x in context["tag_counts"] if x[0] in Tag.get_meta_tags(self.request.user)]

        context["doctypes"] = [x[0] for x in context["doctype_counts"]]

        context["kb_tag_detail_current_tab"] = self.request.session.get("kb_tag_detail_current_tab", "")

        context["tag_list"] = self.get_tag_list_js(tag_list)
        if context["tag_list"]:
            context["title"] = f"Search :: Tag Detail :: {', '.join(tag_list)}"
        else:
            context["title"] = "Tag Search"

        return context

    def get_doc_counts(self, tag_list, aggregation):
        tag_counts = {}
        for buckets in aggregation["buckets"]:
            if buckets["key"] not in tag_list:
                tag_counts[buckets["key"]] = buckets["doc_count"]
        import operator
        tag_counts_sorted = sorted(tag_counts.items(), key=operator.itemgetter(1), reverse=True)

        return tag_counts_sorted

    def get_tag_list_js(self, tag_list):

        return [
            {
                "text": tag,
                "is_meta": "true" if tag in Tag.get_meta_tags(self.request.user) else "false",
                "classes": "badge bg-info",
            }
            for tag in
            tag_list
            if tag != ""
        ]


def sort_results(matches):

    # These categories are sorted according to importance and define
    #  the order matches appear in the search results
    types = {
        "Tag": [],
        "Artist": [],
        "Song": [],
        "Album": [],
        "Book": [],
        "Drill": [],
        "Note": [],
        "Bookmark": [],
        "Document": [],
        "Blob": [],
        "Todo": []
    }

    for match in matches:
        types[match["doctype"]].append(match)

    # Remove empty categories
    result = {key: value for (key, value) in types.items() if len(value) > 0}

    response = []
    for key, value in result.items():
        response.extend(
            [
                {
                    "id": f"__{key}",
                    "name": f"{key}s",
                    "splitter": True,
                    "value": "Bogus"
                },
                *result[key]
            ]
        )

    return response


def get_link(doc_type, match):

    if doc_type == "Bookmark":
        return match["url"]
    if doc_type == "Song":
        if "album_uuid" in match:
            return reverse("music:album_detail", kwargs={"uuid": match["album_uuid"]})
        else:
            return reverse("music:artist_detail", kwargs={"artist_uuid": match["artist_uuid"]})
    if doc_type == "Album":
        return reverse("music:album_detail", kwargs={"uuid": match["uuid"]})
    if doc_type == "Artist":
        return reverse("music:artist_detail", kwargs={"artist_uuid": match["artist_uuid"]})
    if doc_type in ("Blob", "Book", "Document", "Note"):
        return reverse("blob:detail", kwargs={"uuid": match["uuid"]})
    if doc_type == "Drill":
        return reverse("drill:detail", kwargs={"uuid": match["uuid"]})
    # if doc_type == "Todo":
    #     return reverse("todo:update", kwargs={"uuid": match["uuid"]})

    return ""


def get_name(doc_type, match):

    if doc_type == "Song":
        return f"{match['title']} - {match['artist']}"
    if doc_type == "Artist":
        return match["artist"]
    if doc_type == "Album":
        return match["title"]
    if doc_type == "Drill":
        return match["question"][:30]

    return match["name"].title()


def get_doctype(match):

    if match["_source"]["doctype"] == "song" and "highlight" in match:
        highlight_fields = list(match["highlight"].keys())

        highlight_fields = [x if x != "name" else "Song" for x in match["highlight"].keys()]
        # There could be multiple highlighted fields. For now,
        #  pick the first one.
        # Remove the subfield ".autocomplete" from the result, so
        #  "artist.autocomplete" becomes "artist".
        return highlight_fields[0].split(".")[0].title()

    return match["_source"]["doctype"].title()


def get_doc_types_from_request(request):

    if request.GET.get("doc_type", "") != "":
        doc_types = request.GET.get("doc_type").split(",")
    else:
        doc_types = []

    # The front-end filter "Music" translates to the two doctypes
    #  "album" and "song" in the Elasticsearch index
    if "music" in doc_types:
        doc_types = ["album", "song"]

    return doc_types


def is_cached():

    cache = {
        "Artist": {},
        "Album": {}
    }

    def check_cache(doctype, value):

        if doctype not in ["Artist", "Album"]:
            return False

        if value in cache[doctype]:
            return True

        cache[doctype][value] = True
        return False

    return check_cache


@login_required
def search_tags_and_names(request):
    """
    Endpoint for top-search "auto-complete" matching tags and names
    """

    search_term = request.GET["term"].lower()

    doc_types = get_doc_types_from_request(request)

    matches = search_names_es(request.user, search_term, doc_types)

    # Add tag search results to the list of matches
    matches.extend(search_tags_es(request.user, search_term, doc_types))

    return JsonResponse(sort_results(matches), safe=False)


def search_tags_es(user, search_term, doc_types):

    es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)

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
                                    "match": {
                                        "tags.autocomplete": {
                                            "query": search_term,
                                            "operator": "and"
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        },
        "aggs": {
            "Distinct Tags": {
                "terms": {
                    "field": "tags.keyword",
                    "size": 1000
                }
            }
        },
        "from": 0, "size": 100,
        "_source": ["album_id",
                    "album",
                    "artist",
                    "author",
                    "date",
                    "date_unixtime",
                    "doctype",
                    "filename",
                    "importance",
                    "name",
                    "question",
                    "sha1sum",
                    "tags",
                    "url",
                    "uuid"]
    }

    if len(doc_types) > 1:
        search_object["query"]["bool"]["must"].append(
            {
                "bool": {
                    "should": [
                        {
                            "term": {
                                "doctype": x
                            }
                        }
                        for x in doc_types
                    ]
                }
            }
        )

    results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

    matches = []
    for tag_result in results["aggregations"]["Distinct Tags"]["buckets"]:
        if tag_result["key"].lower().find(search_term.lower()) != -1:
            matches.insert(0,
                           {
                               "doctype": "Tag",
                               "name": tag_result["key"],
                               "id": tag_result["key"],
                               "link": get_tag_link(tag_result["key"], doc_types)
                           }
                           )

    matches.extend(get_tag_aliases(user, search_term))
    return matches


@login_required
def search_names(request):

    # Limit each search term to 10 characters, since we've configured the
    # Elasticsearch ngram_tokenizer to only analyze tokens up to that many
    # characters (see mappings.json). Otherwise no results will be returned
    # for longer terms.
    #
    # Remove search terms less than 2 characters in length, since the
    # ngram_tokenizer generates tokens that are 2 characters or longer.
    # Therefore shorter tokens won't generate a match based on the ES query used.
    #
    # Search terms are separated by spaces.
    search_term = unquote(request.GET["term"].lower())
    search_term = " ".join([x[:10] for x in re.split(r"\s+", search_term) if len(x) > 1])

    doc_types = get_doc_types_from_request(request)

    matches = search_names_es(request.user, search_term, doc_types)
    return JsonResponse(matches, safe=False)


def search_names_es(user, search_term, doc_types):
    """
    Search Elasticsearch for objects based on a name, or equivalent field (eg title).
    Primarily used by autocomplete inputs.
    """

    es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)

    search_object = {
        "query": {
            "function_score": {
                "field_value_factor": {
                    "field": "importance",
                    "missing": 1
                },
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
                                            "match": {
                                                "name.autocomplete": {
                                                    "query": search_term,
                                                    "operator": "and"
                                                }
                                            }
                                        },
                                        {
                                            "match": {
                                                "question.autocomplete": {
                                                    "query": search_term,
                                                    "operator": "and"
                                                }
                                            }
                                        },
                                        {
                                            "match": {
                                                "title.autocomplete": {
                                                    "query": search_term,
                                                    "operator": "and"
                                                }
                                            }
                                        },
                                        {
                                            "match": {
                                                "artist.autocomplete": {
                                                    "query": search_term,
                                                    "operator": "and"
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
        },
        "highlight": {
            "fields": {
                "name.autocomplete": {},
                "artist.autocomplete": {}
            }
        },
        "from": 0,
        "size": SEARCH_LIMIT,
        "_source": ["album_uuid",
                    "album",
                    "artist",
                    "artist_uuid",
                    "author",
                    "bordercore_id",
                    "date",
                    "date_unixtime",
                    "doctype",
                    "filename",
                    "importance",
                    "name",
                    "note",
                    "question",
                    "sha1sum",
                    "tags",
                    "title",
                    "url",
                    "uuid"]
    }

    if len(doc_types) > 0:

        if "image" in doc_types:
            # 'image' isn't an official ES doctype, so treat this
            #  as a search for a content type that matches an image.
            doc_types.remove("image")
            search_object["query"]["function_score"]["query"]["bool"]["must"].append(
                {
                    "bool": {
                        "should": [
                            {
                                "wildcard": {
                                    "content_type": {
                                        "value": "image/*",
                                    }
                                }
                            }
                        ]
                    }
                }
            )
        elif "media" in doc_types:
            # 'media' isn't an official ES doctype, so treat this
            #  as a search for a content type that matches either
            #  an image or a video
            doc_types.remove("media")
            search_object["query"]["function_score"]["query"]["bool"]["must"].append(
                {
                    "bool": {
                        "should": [
                            {
                                "wildcard": {
                                    "content_type": {
                                        "value": "image/*",
                                    }
                                }
                            },
                            {
                                "wildcard": {
                                    "content_type": {
                                        "value": "video/*",
                                    }
                                }
                            }
                        ]
                    }
                }
            )

        search_object["query"]["function_score"]["query"]["bool"]["must"].append(
            {
                "bool": {
                    "should": [
                        {
                            "term": {
                                "doctype": x
                            }
                        }
                        for x in doc_types
                    ]
                }
            }
        )

    results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)
    matches = []

    cache_checker = is_cached()

    for match in results["hits"]["hits"]:
        doc_type_pretty = get_doctype(match)
        name = get_name(doc_type_pretty, match["_source"])

        if not cache_checker(doc_type_pretty, name):
            if "date_unixtime" in match["_source"] and match["_source"]["date_unixtime"] is not None:
                date = datetime.datetime.fromtimestamp(
                    int(match["_source"]["date_unixtime"])
                ).strftime(
                    "%b %Y"
                )
            else:
                date = ""
            matches.append(
                {
                    "name": name,
                    "date": date,
                    "doctype": doc_type_pretty,
                    "note": match["_source"].get("note", ""),
                    "uuid": match["_source"].get("uuid"),
                    "id": match["_source"].get("uuid"),
                    "important": match["_source"].get("importance"),
                    "url": match["_source"].get("url", None),
                    "link": get_link(doc_type_pretty, match["_source"]),
                    "score": match["_score"]
                }
            )
            if doc_type_pretty in ["Blob", "Book", "Document"]:
                matches[-1]["cover_url"] = Blob.get_cover_url_static(
                    match["_source"].get("uuid"),
                    match["_source"].get("filename"),
                    size="small"
                )
                matches[-1]["type"] = "blob"
            if doc_type_pretty == "Bookmark":
                matches[-1]["cover_url"] = Bookmark.thumbnail_url_static(
                    match["_source"].get("uuid"),
                    match["_source"].get("url"),
                )
                matches[-1]["type"] = "bookmark"

    return matches
