import math
import re

import markdown
from elasticsearch import Elasticsearch
from markdown.extensions.codehilite import CodeHiliteExtension

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView

from blob.models import Blob
from lib.time_utils import get_date_from_pattern, get_relative_date
from lib.util import truncate
from tag.models import Tag


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


@method_decorator(login_required, name='dispatch')
class SearchListView(ListView):

    template_name = 'search/search.html'
    context_object_name = 'search_results'
    RESULT_COUNT_PER_PAGE = 100

    def get_paginator(self, page, object_list):

        paginator = {
            "number": page,
            "num_pages": int(math.ceil(object_list["hits"]["total"]["value"] / self.RESULT_COUNT_PER_PAGE)),
            "total_results": object_list["hits"]["total"]["value"]
        }

        paginator["has_previous"] = True if page != 1 else False
        paginator["has_next"] = True if page != paginator["num_pages"] else False

        paginator["previous_page_number"] = page - 1
        paginator["next_page_number"] = page + 1

        return paginator

    def get_hit_count(self):

        hit_count = self.request.GET.get("rows", None)

        if hit_count == "No limit":
            hit_count = 1000000
        elif hit_count is None:
            hit_count = self.RESULT_COUNT_PER_PAGE

        return hit_count

    def get_aggregations(self, context, aggregation):

        aggregations = []
        for x in context["search_results"]["aggregations"][aggregation]["buckets"]:
            aggregations.append({"doctype": x["key"], "count": x["doc_count"]})
        return aggregations

    def get_queryset(self, **kwargs):

        # Store the "sort" field in the user's session
        self.request.session["search_sort_by"] = self.request.GET.get("sort", None)

        search_term = self.request.GET.get("search", None)
        sort_field = self.request.GET.get("sort", "date_unixtime")
        hit_count = self.get_hit_count()
        boolean_type = self.request.GET.get("boolean_search_type", "AND")
        doctype = self.request.GET.get("doctype", None)

        es = Elasticsearch(
            [settings.ELASTICSEARCH_ENDPOINT],
            verify_certs=False
        )

        search_object = {
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
            },
            "aggs": {
                "Doctype Filter": {
                    "terms": {
                        "field": "doctype",
                        "size": 10,
                    }
                }
            },
            "sort": {sort_field: {"order": "desc"}},
            "from": 0, "size": hit_count,
            "_source": ["artist",
                        "author",
                        "bordercore_id",
                        "date",
                        "date_unixtime",
                        "doctype",
                        "filepath",
                        "importance",
                        "last_modified",
                        "name",
                        "question",
                        "sha1sum",
                        "tags",
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
            search_object["query"]["bool"]["must"].append(
                {
                    "multi_match": {
                        "type": "phrase" if self.request.GET.get("exact_match", None) in ["Yes"] else "best_fields",
                        "query": search_term,
                        "fields": ["answer", "artist", "author", "attachment.content", "contents", "name", "question", "sha1sum", "uuid"],
                        "operator": boolean_type,
                    }
                }
            )

        results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

        # Django templates don't allow variables with underscores, so
        #  change the "_source" key to "source"
        for index, x in enumerate(results["hits"]["hits"]):
            t = results["hits"]["hits"][index]
            t["source"] = t.pop("_source")

        return results

    def refine_search(self, search_object):
        return search_object

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        if "doctype" in self.request.GET:
            context["doctype_filter"] = self.request.GET["doctype"].split(",")

        if context["search_results"]:

            for match in context["search_results"]["hits"]["hits"]:

                # if match["source"]["doctype"] == "note":
                #     if context["info"]["highlighting"][match["id"]].get("document_body"):
                #         note = context["info"]["highlighting"][match["id"]]["document_body"][0]

                match["source"]["creators"] = get_creators(match["source"])
                match["source"]["date"] = get_date_from_pattern(match["source"].get("date", None))
                match["source"]["last_modified"] = get_relative_date(match["source"]["last_modified"])

            context["aggregations"] = self.get_aggregations(context, "Doctype Filter")

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

        search_object["query"]["bool"]["must"].append(
            {
                "term": {
                    "doctype": "note"
                }
            }
        )

        tagsearch = self.request.GET.get("tagsearch", None)
        if tagsearch:
            search_object["query"]["bool"]["must"].append(
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
        context["paginator"] = self.get_paginator(page, context["search_results"])
        context["pinned_notes"] = self.request.user.userprofile.pinned_notes.all().only("name", "uuid").order_by("sortorderusernote__sort_order")

        for match in context["search_results"]["hits"]["hits"]:

            match["source"]["content"] = markdown.markdown(
                match["source"]["contents"],
                extensions=[CodeHiliteExtension(guess_lang=False), "tables"]
            )

        return context


@method_decorator(login_required, name="dispatch")
class SearchTagDetailView(ListView):

    template_name = "search/tag_detail.html"
    RESULT_COUNT_PER_PAGE = 100
    context_object_name = "search_results"

    def get_queryset(self):

        taglist = self.kwargs.get("taglist", "").split(",")
        hit_count = 1000

        es = Elasticsearch(
            [settings.ELASTICSEARCH_ENDPOINT],
            verify_certs=False
        )

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
                "bool": {
                    "must": tag_query
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
            "sort": {"last_modified": {"order": "desc"}},
            "from": 0, "size": hit_count,
            "_source": ["artist",
                        "author",
                        "content_type",
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
                        "url",
                        "uuid"]
        }

        results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)
        return results

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        results = {}
        for match in context["search_results"]["hits"]["hits"]:

            result = {
                "artist": match["_source"].get("artist", ""),
                "question": truncate(match["_source"].get("question", "")),
                "name": match["_source"].get("name", "No Name"),
                "task": match["_source"].get("name", ""),
                "url": match["_source"].get("url", ""),
                "uuid": match["_source"].get("uuid", "")
            }
            if match["_source"].get("sha1sum", ""):

                result = {
                    "sha1sum": match["_source"]["sha1sum"],
                    "filename": match["_source"].get("filename", ""),
                    "url": Blob.get_s3_key_from_sha1sum(
                        match["_source"]["sha1sum"],
                        match["_source"].get("filename", "")
                    ),
                    "cover_url": Blob.get_cover_info_static(
                        self.request.user,
                        match["_source"]["sha1sum"],
                        size="small"
                    )["url"],
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
                "value": tag,
                "is_meta": "true" if tag in Tag.get_meta_tags(self.request.user) else "false",
                "classes": "badge badge-primary",
            }
            for tag in
            tag_list
            if tag != ""
        ]


def sort_results(matches):

    types = {
        "Tag": [],
        "Song": [],
        "Artist": [],
        "Album": [],
        "Book": [],
        "Drill": [],
        "Note": [],
        "Bookmark": [],
        "Document": [],
        "Blob": [],
    }

    for match in matches:
        types[match["object_type"]].append(match)

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
    elif doc_type == "Song":
        if "album_uuid" in match:
            return reverse("music:album_detail", kwargs={"uuid": match["album_uuid"]})
        else:
            return reverse("music:artist_detail", kwargs={"artist": match["artist"]})
    elif doc_type == "Artist":
        return reverse("music:artist_detail", kwargs={"artist": match["artist"]})
    elif doc_type == "Album":
        return reverse("music:album_detail", kwargs={"uuid": match["album_uuid"]})
    elif doc_type in ("Blob", "Book", "Document", "Note"):
        return reverse("blob:detail", kwargs={"uuid": match["uuid"]})
    elif doc_type == "Drill":
        return reverse("drill:detail", kwargs={"uuid": match["uuid"]})
    else:
        return ""


def get_tag_link(doc_type, tag):

    if doc_type == "note":
        return reverse("search:notes") + f"?tagsearch={tag}"
    elif doc_type == "bookmark":
        return reverse("bookmark:get_bookmarks_by_tag", kwargs={"tag_filter": tag})
    elif doc_type == "drill":
        return reverse("drill:study_tag", kwargs={"tag": tag})
    elif doc_type == "song":
        return reverse("music:search_tag") + f"?tag={tag}"
    else:
        return reverse("search:kb_search_tag_detail", kwargs={"taglist": tag})


def get_name(doc_type, match):
    if doc_type == "Song":
        return f"{match['title']} - {match['artist']}"
    elif doc_type == "Artist":
        return match["artist"]
    elif doc_type == "Album":
        return match["album"]
    elif doc_type == "Drill":
        return match["question"][:30]
    else:
        return match["name"].title()


def get_doctype(match):

    if match["_source"]["doctype"] == "song" and "highlight" in match:
        highlight_fields = list(match["highlight"].keys())

        highlight_fields = [x if x != "name" else "Song" for x in match["highlight"].keys()]
        # There could be multiple highlighted fields. For now,
        #  pick the first one.
        return highlight_fields[0].title()
    else:
        return match["_source"]["doctype"].title()


def is_cached():

    cache = {
        "Artist": {},
        "Album": {}
    }

    def check_cache(object_type, value):

        if object_type not in ["Artist", "Album"]:
            return False

        if value in cache[object_type]:
            return True

        cache[object_type][value] = True
        return False

    return check_cache


@login_required
def search_tags_and_names(request):
    """
    Endpoint for top-search "auto-complete" matching tags and names
    """

    es = Elasticsearch(
        [settings.ELASTICSEARCH_ENDPOINT],
        verify_certs=False
    )

    search_term = request.GET["term"].lower()
    doc_type = request.GET.get("filter", None)

    # The front-end filter is a catch-all "Music", but the actual
    #  Elasticsearch doctype is "song"
    if doc_type == "music":
        doc_type = "song"

    results_name = search_names(request, es, doc_type, search_term)

    matches = []

    cache_checker = is_cached()

    for match in results_name["hits"]["hits"]:
        object_type = get_doctype(match)
        name = get_name(object_type, match["_source"])

        if not cache_checker(object_type, name):
            matches.append(
                {
                    "object_type": object_type,
                    "value": name,
                    "uuid": match["_source"].get("uuid"),
                    "id": match["_id"],
                    "url": match["_source"].get("url", None),
                    "link": get_link(object_type, match["_source"])
                }
            )

    # Add tag search results to the list of matches
    matches.extend(search_tags(request, es, doc_type, search_term))

    return JsonResponse(sort_results(matches), safe=False)


@login_required
def search_names(request, es, doc_type, search_term):

    search_terms = re.split(r"\s+", search_term)

    search_object = {
        "query": {
            "bool": {
                "must": [
                    {
                        "term": {
                            "user_id": request.user.id
                        }
                    }
                ]
            }
        },
        "from": 0, "size": 100,
        "_source": ["album_uuid",
                    "album",
                    "artist",
                    "author",
                    "bordercore_id",
                    "date",
                    "date_unixtime",
                    "doctype",
                    "filepath",
                    "importance",
                    "name",
                    "question",
                    "sha1sum",
                    "tags",
                    "url",
                    "uuid"]
    }

    # Separate query into terms based on whitespace and
    #  and treat it like an "AND" boolean search
    for one_term in search_terms:
        search_object["query"]["bool"]["must"].append(
            {
                "bool": {
                    "should": [
                        {
                            "wildcard": {
                                "name": {
                                    "value": f"*{one_term}*",
                                }
                            }
                        },
                        {
                            "wildcard": {
                                "album": {
                                    "value": f"*{one_term}*",
                                }
                            }
                        },
                        {
                            "wildcard": {
                                "artist": {
                                    "value": f"*{one_term}*",
                                }
                            }
                        },
                        {
                            "wildcard": {
                                "question": {
                                    "value": f"*{one_term}*",
                                }
                            }
                        }
                    ]
                }
            }
        )

    search_object["highlight"] = {
        "fields": {
            "album": {},
            "name": {},
            "artist": {}
        }
    }

    if doc_type:
        search_object["query"]["bool"]["must"].append(
            {
                "term": {
                    "doctype": doc_type
                }
            },
        )

    return es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)


@login_required
def search_tags(request, es, doc_type, search_term):

    search_object = {
        "query": {
            "bool": {
                "must": [
                    {
                        "term": {
                            "user_id": request.user.id
                        }
                    },
                    {
                        "wildcard": {
                            "tags": f"{search_term}*"
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
                    "filepath",
                    "importance",
                    "name",
                    "question",
                    "sha1sum",
                    "tags",
                    "url",
                    "uuid"]
    }

    if doc_type:
        search_object["query"]["bool"]["must"].append(
            {
                "term": {
                    "doctype": doc_type
                }
            },
        )

    results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

    matches = []
    for tag_result in results["aggregations"]["Distinct Tags"]["buckets"]:
        if tag_result["key"].lower().find(search_term.lower()) != -1:
            matches.insert(0,
                           {
                               "object_type": "Tag",
                               "value": tag_result["key"],
                               "id": tag_result["key"],
                               "link": get_tag_link(doc_type, tag_result["key"]),
                           }
                           )

    return matches
