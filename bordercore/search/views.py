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
from lib.time_utils import get_date_from_pattern, get_relative_date
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

    SECTION = 'search'
    SUB_SECTION = 'home'
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

    # def get_facet_query(self, facet, term):

    #     if facet == 'Blobs':
    #         return 'doctype:blob'
    #     elif facet == 'Books':
    #         return 'doctype:book'
    #     elif facet == 'Documents':
    #         return 'doctype:document'
    #     elif facet == 'Todos':
    #         return 'doctype:todo'
    #     elif facet == 'Notes':
    #         return 'doctype:note'
    #     elif facet == 'Links':
    #         return 'doctype:bookmark'
    #     elif facet == 'Titles':
    #         return '(title:{})'.format(term)
    #     elif facet == 'Tags':
    #         return 'tags:{}'.format(term)

    def get_hit_count(self):

        hit_count = self.request.GET.get("rows", None)

        if hit_count == "No limit":
            hit_count = 1000000
        elif hit_count is None:
            hit_count = self.RESULT_COUNT_PER_PAGE

        return hit_count

    def get_queryset(self, **kwargs):

        # Store the "sort" field in the user's session
        self.request.session["search_sort_by"] = self.request.GET.get("sort", None)

        search_term = self.request.GET.get("search", None)
        sort_field = self.request.GET.get("sort", "date_unixtime")
        hit_count = self.get_hit_count()
        boolean_type = self.request.GET.get("boolean_search_type", "AND")

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

        # Let subclasses modify the query
        search_object = self.refine_search(search_object)

        if search_term:
            search_object["query"]["bool"]["must"].append(
                {
                    "multi_match": {
                        "type": "best_fields" if not self.request.GET.get("exact_match", None) else "phrase",
                        "query": search_term,
                        "fields": ["artist", "author", "attachment.content", "contents", "sha1sum", "task", "title", "uuid"],
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

        context = super(SearchListView, self).get_context_data(**kwargs)

        # facet_counts = {}

        # if self.request.GET.get("facets"):
        #     context["filter_query"] = self.request.GET.get("facets").split(",")

        if context["search_results"]:

            # for k, v in context["info"]["facet_counts"]["facet_queries"].items():
            #     if v > 0:
            #         facet_counts[k] = v

            for match in context["search_results"]["hits"]["hits"]:

                # if match["source"]["doctype"] == "note":
                #     if context["info"]["highlighting"][match["id"]].get("document_body"):
                #         note = context["info"]["highlighting"][match["id"]]["document_body"][0]

                match["source"]["creators"] = get_creators(match["source"])
                match["source"]["date"] = get_date_from_pattern(match["source"].get("date", None))
                match["source"]["last_modified"] = get_relative_date(match["source"]["last_modified"])

            # Convert to a list of dicts.  This lets us use the dictsortreversed
            #  filter in our template to sort by count.
            # context["facet_counts"] = [{"doctype_purty": k, "doctype": k, "count": v} for k, v in facet_counts.items()]

        context["section"] = self.SECTION
        context["subsection"] = self.SUB_SECTION
        context["title"] = "Search"
        return context


@method_decorator(login_required, name="dispatch")
class NoteListView(SearchListView):

    SECTION = "notes"
    SUB_SECTION = None
    template_name = "blob/note_list.html"
    RESULT_COUNT_PER_PAGE_NOTE = 10

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

        context = super(NoteListView, self).get_context_data(**kwargs)

        page = int(self.request.GET.get("page", 1))
        context["paginator"] = self.get_paginator(page, context["search_results"])
        context["favorite_notes"] = self.request.user.userprofile.favorite_notes.all().only("title", "uuid").order_by("sortorderusernote__sort_order")

        for match in context["search_results"]["hits"]["hits"]:

            match["source"]["content"] = markdown.markdown(
                match["source"]["contents"],
                extensions=[CodeHiliteExtension(guess_lang=False), "tables"]
            )

        return context


@method_decorator(login_required, name="dispatch")
class SearchTagDetailView(ListView):

    template_name = "search/tag_detail.html"
    SECTION = "search"
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

        context["meta_tags"] = [x for x in tag_counts if x in Tag.get_meta_tags(self.request.user)]

        import operator
        tag_counts_sorted = sorted(tag_counts.items(), key=operator.itemgetter(1), reverse=True)
        context["tag_counts"] = tag_counts_sorted
        doctype_counts_sorted = sorted(doctype_counts.items(), key=operator.itemgetter(1), reverse=True)
        context["doctype_counts"] = doctype_counts_sorted

        # TODO: Use dictionary comprehension?
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
                        "value": tag,
                        "is_meta": "true" if tag in Tag.get_meta_tags(self.request.user) else "false",
                        "classes": "badge badge-primary",
                    }
                )
        context["tag_list"] = tag_list_js

        context["kb_tag_detail_current_tab"] = self.request.session.get("kb_tag_detail_current_tab", "")
        context["section"] = self.SECTION
        context["subsection"] = "search-tag"

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
def search_tags_and_titles(request):

    es = Elasticsearch(
        [settings.ELASTICSEARCH_ENDPOINT],
        verify_certs=False
    )

    search_term = request.GET["term"]
    doc_type = request.GET.get("doc_type", None)

    search_terms = re.split(r"\s+", request.GET["term"])

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
        "from": 0, "size": 50,
        "_source": ["author",
                    "date",
                    "date_unixtime",
                    "doctype",
                    "filepath",
                    "importance",
                    "sha1sum",
                    "tags",
                    "title",
                    "url",
                    "uuid"]
    }

    # Separate query into terms based on whitespace and
    #  and treat it like an "AND" boolean search
    for one_term in search_terms:
        search_object["query"]["bool"]["must"].append(
            {
                "wildcard": {
                    "title.raw": {
                        "value": f"*{one_term}*",
                    }
                }
            },
        )

    if doc_type:

        search_object["query"]["bool"]["must"].append(
            {
                "term": {
                    "doctype": doc_type
                }
            },
        )

    results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

    tags = {}
    matches = []

    for match in results["hits"]["hits"]:

        matches.append(
            {
                "object_type": match["_source"]["doctype"].title(),
                "value": match["_source"]["title"],
                "uuid": match["_source"].get("uuid"),
                "id": match["_id"],
                "url": match["_source"].get("url", None)
            }
        )

        if "tags" in match["_source"]:
            for tag in [x for x in match["_source"]["tags"] if x.lower().find(search_term.lower()) != -1]:
                tags[tag] = 1

    for tag in tags:
        matches.insert(0, {"object_type": "Tag", "value": tag, "id": tag})

    return JsonResponse(matches, safe=False)
