import math
import re

import markdown
from elasticsearch import Elasticsearch
from markdown.extensions.codehilite import CodeHiliteExtension

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView

from blob.models import Blob
from lib.time_utils import get_relative_date
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

    template_name = 'kb/search.html'
    SECTION = 'kb'
    context_object_name = 'info'
    RESULT_COUNT_PER_PAGE = 100
    RESULT_COUNT_PER_PAGE_NOTE = 10

    def get_paginator(self, page, object_list):

        paginator = {
            "number": page,
            "num_pages": int(math.ceil(object_list["hits"]["total"]["value"] / self.RESULT_COUNT_PER_PAGE_NOTE)),
            "total_results": object_list["hits"]["total"]["value"]
        }

        paginator["has_previous"] = True if page != 1 else False
        paginator["has_next"] = True if page != paginator["num_pages"] else False

        paginator["previous_page_number"] = page - 1
        paginator["next_page_number"] = page + 1

        return paginator

    def get_facet_query(self, facet, term):

        if facet == 'Blobs':
            return 'doctype:blob'
        elif facet == 'Books':
            return 'doctype:book'
        elif facet == 'Documents':
            return 'doctype:document'
        elif facet == 'Todos':
            return 'doctype:todo'
        elif facet == 'Notes':
            return 'doctype:note'
        elif facet == 'Links':
            return 'doctype:bordercore_bookmark'
        elif facet == 'Titles':
            return '(title:{})'.format(term)
        elif facet == 'Tags':
            return 'tags:{}'.format(term)

    def get_queryset(self, **kwargs):

        page = int(self.request.GET.get("page", 1))

        notes_search = True if self.kwargs.get("notes_search", "") else False

        if notes_search:
            self.RESULT_COUNT_PER_PAGE = self.RESULT_COUNT_PER_PAGE_NOTE

        if "search" in self.request.GET or notes_search:

            if not notes_search:
                # Store the "sort" field in the user's session
                self.request.session["search_sort_by"] = self.request.GET.get("sort", None)

            search_term = escape_solr_terms(self.request.GET.get("search", ""))
            sort_field = self.request.GET.get("sort", "date_unixtime")

            hit_count = self.request.GET.get("rows", None)
            boolean_type = self.request.GET.get("boolean_search_type", "AND")

            if hit_count == "No limit":
                hit_count = 1000000
            elif hit_count is None:
                hit_count = self.RESULT_COUNT_PER_PAGE

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
                "sort": {sort_field: {"order": "desc"}},
                "from": 0, "size": hit_count,
                "_source": ["artist",
                            "author",
                            "bordercore_id",
                            "task",
                            "date",
                            "date_unixtime",
                            "doctype",
                            "filepath",
                            "importance",
                            "bordercore_id",
                            "last_modified",
                            "sha1sum",
                            "tags",
                            "title",
                            "url",
                            "uuid"]
            }

            if notes_search:

                search_object["from"] = (page - 1) * self.RESULT_COUNT_PER_PAGE_NOTE

                # Only retrieve the contents for notes, which should be
                #  relatively small
                search_object["_source"].append("contents")

                search_object["query"]["bool"]["must"].append(
                    {
                        "term": {
                            "doctype": "note"
                        }
                    }
                )

                tagsearch = self.request.GET.get("tagsearch", "")
                if tagsearch:
                    search_object["query"]["bool"]["must"].append(
                        {
                            "term": {
                                "tags.keyword": tagsearch
                            }
                        }
                    )

            if search_term:
                search_object["query"]["bool"]["must"].append(
                    {
                        "multi_match": {
                            "query": search_term,
                            "fields": ["artist", "author", "attachment.content", "contents", "sha1sum", "task", "title", "uuid"],
                            "operator": boolean_type,
                        }
                    }
                )

            results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)
            return results

    def get_context_data(self, **kwargs):

        context = super(SearchListView, self).get_context_data(**kwargs)
        notes_search = True if self.kwargs.get("notes_search", "") else False

        if notes_search:
            self.SECTION = "notes"
            self.template_name = "blob/note_list.html"
            page = int(self.request.GET.get("page", 1))
            context["paginator"] = self.get_paginator(page, context["info"])
            context["favorite_notes"] = self.request.user.userprofile.favorite_notes.all().only("title", "uuid").order_by("sortordernote__sort_order")

        info = []
        facet_counts = {}

        if self.request.GET.get("facets"):
            context["filter_query"] = self.request.GET.get("facets").split(",")

        if context["info"]:

            # for k, v in context["info"]["facet_counts"]["facet_queries"].items():
            #     if v > 0:
            #         facet_counts[k] = v

            from lib.time_utils import get_date_from_pattern

            for myobject in context["info"]["hits"]["hits"]:
                note = ""
                # if myobject["_source"]["doctype"] == "note":
                #     if context["info"]["highlighting"][myobject["id"]].get("document_body"):
                #         note = context["info"]["highlighting"][myobject["id"]]["document_body"][0]

                match = dict(
                    title=myobject["_source"].get("title", "No Title"),
                    creators=get_creators(myobject["_source"]),
                    date=get_date_from_pattern(myobject["_source"].get("date", None)),
                    doctype=myobject["_source"]["doctype"],
                    sha1sum=myobject["_source"].get("sha1sum", ""),
                    uuid=myobject["_source"].get("uuid", ""),
                    id=myobject["_id"],
                    importance=myobject["_source"].get("importance", ""),
                    last_modified=get_relative_date(myobject["_source"]["last_modified"]),
                    url=myobject["_source"].get("url", ""),
                    filename=myobject["_source"].get("filename", ""),
                    tags=myobject["_source"].get("tags"),
                    task=myobject["_source"].get("task", ""),
                    bordercore_id=myobject["_source"].get("bordercore_id", None),
                    note=note
                )

                if notes_search:
                    match["content"] = markdown.markdown(myobject["_source"]["contents"], extensions=[CodeHiliteExtension(guess_lang=False), "tables"])

                info.append(match)

            context["numFound"] = context["info"]["hits"]["total"]["value"]

            # Convert to a list of dicts.  This lets us use the dictsortreversed
            #  filter in our template to sort by count.
            # context["facet_counts"] = [{"doctype_purty": k, "doctype": k, "count": v} for k, v in facet_counts.items()]

        context["info"] = info
        context["section"] = self.SECTION
        context["nav"] = "search-home"
        context["title"] = "Search"
        return context


@method_decorator(login_required, name="dispatch")
class SearchTagDetailView(ListView):

    template_name = "kb/tag_detail.html"
    SECTION = "kb"
    RESULT_COUNT_PER_PAGE = 100
    context_object_name = "info"

    def get_context_data(self, **kwargs):

        context = super(SearchTagDetailView, self).get_context_data(**kwargs)
        results = {}
        for myobject in context["info"]["hits"]["hits"]:

            match = dict(
                title=myobject["_source"].get("title", "No Title"),
                task=myobject["_source"].get("task", ""),
                url=myobject["_source"].get("url", ""),
                uuid=myobject["_source"].get("uuid", "")
            )
            if myobject["_source"].get("sha1sum", ""):
                match["sha1sum"] = myobject["_source"].get("sha1sum", "")
                match["filename"] = myobject["_source"].get("filename", "")
                match["url"] = Blob.get_s3_key_from_sha1sum(match["sha1sum"], match["filename"])
                match["cover_url"] = Blob.get_cover_info(
                    self.request.user,
                    myobject["_source"]["sha1sum"],
                    size="small"
                )["url"]
                if myobject["_source"].get("content_type", None):
                    match["content_type"] = Blob.get_content_type(myobject["_source"]["content_type"])

            if results.get(myobject["_source"]["doctype"], ""):
                results[myobject["_source"]["doctype"]].append(match)
            else:
                results[myobject["_source"]["doctype"]] = [match]
        context["info"]["matches"] = results

        tag_counts = {}
        tag_list = self.kwargs.get("taglist", "").split(",")
        for buckets in context["info"]["aggregations"]["Tag Filter"]["buckets"]:
            if buckets["key"] not in tag_list:
                tag_counts[buckets["key"]] = buckets["doc_count"]
        doctype_counts = {}
        for buckets in context["info"]["aggregations"]["Doctype Filter"]["buckets"]:
            if buckets["key"] not in tag_list:
                doctype_counts[buckets["key"]] = buckets["doc_count"]

        meta_tags = [x for x in tag_counts if x in Tag.get_meta_tags(self.request.user)]
        context["meta_tags"] = meta_tags

        import operator
        tag_counts_sorted = sorted(tag_counts.items(), key=operator.itemgetter(1), reverse=True)
        context["tag_counts"] = tag_counts_sorted
        doctype_counts_sorted = sorted(doctype_counts.items(), key=operator.itemgetter(1), reverse=True)
        context["doctype_counts"] = doctype_counts_sorted

        doctypes = {}
        for x in doctype_counts.keys():
            doctypes[x] = 1
        context["doctypes"] = doctypes

        tag_list_js = []
        for tag in tag_list:
            if tag != "":
                tag_list_js.append(
                    {
                        "text": tag,
                        "is_meta": "true" if tag in Tag.get_meta_tags(self.request.user) else "false",
                        "classes": "badge badge-primary",
                    }
                )
        context["tag_list"] = tag_list_js

        context["kb_tag_detail_current_tab"] = self.request.session.get("kb_tag_detail_current_tab", "")
        context["section"] = self.SECTION
        context["nav"] = "search-tag"

        if context["tag_list"]:
            context["title"] = "Search :: Tag Detail :: {}".format(", ".join(tag_list))
        else:
            context["title"] = "Tag Search"

        return context

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
                        "field": "doctype.keyword",
                        "size": 10
                    }
                },
                "Tag Filter": {
                    "terms": {
                        "field": "tags.keyword",
                        "size": 10
                    }
                }
            },
            "sort": {"last_modified": {"order": "desc"}},
            "from": 0, "size": hit_count,
            "_source": ["author",
                        "task",
                        "content_type",
                        "date",
                        "date_unixtime",
                        "doctype",
                        "filename",
                        "importance",
                        "bordercore_id",
                        "last_modified",
                        "sha1sum",
                        "tags",
                        "title",
                        "url",
                        "uuid"]
        }

        results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)
        return results


@login_required
def kb_search_tags_booktitles(request):

    es = Elasticsearch(
        [settings.ELASTICSEARCH_ENDPOINT],
        verify_certs=False
    )

    search_term = escape_solr_terms(handle_quotes(request, request.GET['term']))

    search_object = {
        'query': {
            'bool': {
                'must': [
                    {
                        'term': {
                            'doctype': 'book'
                        }
                    },
                    {
                        "wildcard": {
                            "title.raw": {
                                "value": f"*{search_term}*",
                            }
                        }
                    },
                    {
                        'term': {
                            'user_id': request.user.id
                        }
                    }
                ]
            }
        },
        "from": 0, "size": 20,
        "_source": ["author",
                    "date",
                    "date_unixtime",
                    "doctype",
                    "filepath",
                    "importance",
                    "sha1sum",
                    "tags",
                    "title",
                    "uuid"]
    }

    results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

    tags = {}
    matches = []

    for match in results["hits"]["hits"]:

        if match["_source"]["doctype"] == "book":
            matches.append(
                {
                    "type": "Book",
                    "value": match["_source"]["title"],
                    "uuid": match["_source"].get("uuid")
                }
            )

        if match["_source"].get("tags", ""):
            for tag in [x for x in match["_source"]["tags"] if x.lower().startswith(search_term.lower())]:
                tags[tag] = 1

    for tag in tags:
        matches.append({"type": "Tag", "value": tag})

    return JsonResponse(matches, safe=False)


def escape_solr_terms(term):
    """Escape special characters used by Solr with a backslash"""
    return re.sub(r"([:\[\]\{\}\(\)-])", r"\\\1", term)


def handle_quotes(request, search_term):
    """Remove quotes to avoid Solr errors. Support the 'Exact Match' search option."""
    search_term = search_term.replace("\"", "")
    if request.GET.get('exact_match'):
        search_term = "\"{}\"".format(search_term)
    return search_term
