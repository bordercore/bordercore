import json
import os
import re
import urllib
from os.path import basename

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.views.generic.list import ListView

from blob.models import Document
from search.solr import SolrResultSet
from solrpy.core import SolrConnection, SolrException
from tag.models import Tag

SECTION = 'KB'


class SearchListView(ListView):

    template_name = 'kb/search.html'
    SOLR_COUNT_PER_PAGE = 100
    context_object_name = 'info'

    def get_facet_query(self, facet, term):

        if facet == 'Blobs':
            return 'doctype:blob'
        elif facet == 'Books':
            return 'doctype:book'
        elif facet == 'Documents':
            return 'doctype:document'
        elif facet == 'Todos':
            return 'doctype:bordercore_todo'
        elif facet == 'Blog Posts':
            return 'doctype:bordercore_blog'
        elif facet == 'Links':
            return 'doctype:bordercore_bookmark'
        elif facet == 'Titles':
            return '(title:{})'.format(term)
        elif facet == 'Tags':
            return 'tags:{}'.format(term)

    def get_queryset(self):

        if 'search' in self.request.GET:

            search_term = escape_solr_terms(self.request.GET['search'])
            sort = self.request.GET['sort']

            rows = self.request.GET.get('rows', None)
            boolean_type = self.request.GET.get('boolean_search_type', 'AND')
            if rows == 'No limit':
                rows = 1000000
            elif rows is None:
                rows = self.SOLR_COUNT_PER_PAGE

            conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))

            solr_args = {'boost': 'importance',
                         'defType': 'edismax',
                         'fl': 'author,bordercore_todo_task,date,date_unixtime,doctype,filepath,id,importance,internal_id,last_modified,sha1sum,tags,title,url,uuid',
                         'facet': 'on',
                         'facet.mincount': '1',
                         'rows': rows,
                         'sort': sort + ' desc'
                         }

            p = re.compile("^[0-9a-f]{40}$")
            if p.search(search_term):
                solr_args['q'] = 'sha1sum:%s' % (search_term)
            else:

                search_term = handle_quotes(self.request, search_term)
                search_term = search_term + " AND user_id:{}".format(self.request.user.id)

                solr_args.update(
                    {'q': search_term,
                     'q.op': boolean_type,
                     'qf': 'text',
                     'hl': 'true',
                     'hl.fl': 'attr_content,bordercore_todo_task,title',
                     'hl.simple.pre': '<span class="search_bordercore_blogpost_snippet">',
                     'hl.simple.post': '</span>'}
                )

            facet_queries = []
            for facet in ['Blobs', 'Blog Posts', 'Books', 'Titles', 'Documents', 'Links', 'Tags', 'Todos']:
                facet_queries.append('{!key="%s" ex=dt}' % (facet) + self.get_facet_query(facet, search_term))
                solr_args['facet.query'] = facet_queries

            if self.request.GET.get('facets'):
                solr_args['fq'] = '{!tag=dt}' + ' OR '.join([self.get_facet_query(x, search_term) for x in self.request.GET.get('facets').split(',')])

            try:
                results = conn.raw_query(**solr_args)
                return json.loads(results.decode('UTF-8'))
            except (SolrException, ConnectionRefusedError) as e:
                messages.add_message(self.request, messages.ERROR, "Solr error: {}".format(e.strerror))

    def get_context_data(self, **kwargs):
        context = super(SearchListView, self).get_context_data(**kwargs)

        info = []
        facet_counts = {}

        if self.request.GET.get('facets'):
            context['filter_query'] = self.request.GET.get('facets').split(',')

        from solrpy.core import utc_from_string
        from lib.time_utils import get_relative_date

        if context['info']:

            for k, v in context['info']['facet_counts']['facet_queries'].items():
                if v > 0:
                    facet_counts[k] = v

            from lib.time_utils import get_date_from_pattern

            for myobject in context['info']['response']['docs']:
                solr_result_set = SolrResultSet(myobject)
                filename = ''
                last_modified = ''
                blogpost_snippet = ''
                # TODO: Handle matches with multiple titles
                if myobject.get('last_modified'):
                    last_modified = get_relative_date(utc_from_string(myobject.get('last_modified')))
                if myobject.get('filepath'):
                    filename = os.path.basename(myobject['filepath'])
                if myobject['doctype'] == 'blob' and not myobject.get('title', ''):
                    myobject['title'] = [filename]
                if myobject['doctype'] == 'bordercore_blog':
                    if context['info']['highlighting'][myobject['id']].get('attr_content'):
                        blogpost_snippet = context['info']['highlighting'][myobject['id']]['attr_content'][0]
                info.append(dict(title=solr_result_set.get_title(),
                                 author=myobject.get('author', ['']),
                                 date=get_date_from_pattern(myobject.get('date','')),
                                 doctype=myobject['doctype'],
                                 sha1sum=myobject.get('sha1sum', ''),
                                 uuid=myobject.get('uuid', ''),
                                 id=myobject['id'],
                                 importance=myobject.get('importance', ''),
                                 internal_id=myobject.get('internal_id', ''),
                                 last_modified=last_modified,
                                 url=myobject.get('url', ''),
                                 filename=filename,
                                 tags=myobject.get('tags'),
                                 bordercore_todo_task=myobject.get('bordercore_todo_task', ''),
                                 blogpost_snippet=blogpost_snippet,
                             ))
            context['numFound'] = context['info']['response']['numFound']

            # Convert to a list of dicts.  This lets us use the dictsortreversed
            #  filter in our template to sort by count.
            context['facet_counts'] = [{'doctype_purty': k, 'doctype': k, 'count': v} for k, v in facet_counts.items()]

        context['info'] = info
        context['section'] = SECTION
        context['search_sort_by'] = self.request.session.get('search_sort_by', '')
        return context


class SearchTagDetailView(ListView):

    template_name = 'kb/tag_detail.html'
    SOLR_COUNT_PER_PAGE = 100
    context_object_name = 'info'

    def get_context_data(self, **kwargs):
        context = super(SearchTagDetailView, self).get_context_data(**kwargs)
        results = {}
        for one_doc in context['info']['response']['docs']:
            solr_result_set = SolrResultSet(one_doc)
            if one_doc.get('sha1sum', ''):
                one_doc['filename'] = solr_result_set.filename
                one_doc['url'] = one_doc['filepath'].split(settings.MEDIA_ROOT)[1]
                one_doc['cover_url'] = static("blobs/%s/%s/cover-small.jpg" % (one_doc['sha1sum'][0:2], one_doc['sha1sum']))
                if not os.path.isfile("%s/%s/%s/cover-small.jpg" % (settings.MEDIA_ROOT, one_doc['sha1sum'][0:2], one_doc['sha1sum'])):
                    one_doc['cover_url'] = static("images/book.png")
                if one_doc['content_type']:
                    one_doc['content_type'] = Document.get_content_type(one_doc['content_type'][0])
            one_doc['title'] = solr_result_set.get_title()
            if results.get(one_doc['doctype'], ''):
                results[one_doc['doctype']].append(one_doc)
            else:
                results[one_doc['doctype']] = [one_doc]
        context['info']['matches'] = results

        tag_counts = {}
        tag_list = self.kwargs.get('taglist', '').split(',')
        for x, y in grouped(context['info']['facet_counts']['facet_fields']['tags'], 2):
            if x not in tag_list:
                tag_counts[x] = y
        doctype_counts = {}
        for x, y in grouped(context['info']['facet_counts']['facet_fields']['doctype'], 2):
            if x not in tag_list:
                doctype_counts[x] = y

        meta_tags = [x for x in tag_counts if x in Tag.get_meta_tags(self.request.user)]
        context['meta_tags'] = meta_tags

        import operator
        tag_counts_sorted = sorted(tag_counts.items(), key=operator.itemgetter(1), reverse=True)
        context['tag_counts'] = tag_counts_sorted
        doctype_counts_sorted = sorted(doctype_counts.items(), key=operator.itemgetter(1), reverse=True)
        context['doctype_counts'] = doctype_counts_sorted

        doctypes = {}
        for x in doctype_counts.keys():
            doctypes[x] = 1
        context['doctypes'] = doctypes

        tag_list_js = []
        for tag in tag_list:
            if tag != '':
                tag_list_js.append({'name': tag, 'is_meta': 'true' if tag in Tag.get_meta_tags(self.request.user) else 'false'})
        context['tag_list'] = tag_list_js

        context['kb_tag_detail_current_tab'] = self.request.session.get('kb_tag_detail_current_tab', '')
        context['section'] = SECTION

        return context

    def get_queryset(self):
        taglist = self.kwargs.get('taglist', '')
        rows = 1000

        q = ' AND '.join(['tags:"%s"' % (urllib.parse.unquote(t),) for t in taglist.split(',')])
        q = q + ' AND user_id:{}'.format(self.request.user.id)

        conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))

        solr_args = {'q': q,
                     'boost': 'importance',
                     'rows': rows,
                     'fl': 'author,bordercore_todo_task,content_type,doctype,uuid,filepath,id,internal_id,attr_is_book,last_modified,tags,title,sha1sum,url',
                     'facet': 'on',
                     'facet.mincount': '1',
                     'facet.field': ['{!ex=tags}tags', '{!ex=doctype}doctype'],
                     'sort': 'last_modified+desc'
                     }
        results = conn.raw_query(**solr_args)
        return json.loads(results.decode('UTF-8'))


def grouped(iterable, n):
    "s -> (s0,s1,s2,...sn-1), (sn,sn+1,sn+2,...s2n-1), (s2n,s2n+1,s2n+2,...s3n-1), ..."
    return zip(*[iter(iterable)] * n)


@login_required
def search_book_title(request):

    conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))

    title = request.GET['title']

    solr_args = {'q': 'doctype:book AND filepath:*{}* AND user_id:{}'.format(title, request.user.id),
                 'fl': 'id,score,title,author,filepath,uuid'}

    results = conn.raw_query(**solr_args)

    filtered_results = json.loads(results.decode('UTF-8'))

    for match in filtered_results['response']['docs']:
        # If the book doesn't have a title, use the filename
        match['filename'] = os.path.basename(match.get('filepath'))
        if not match.get('title'):
            match['title'] = basename(os.path.splitext(match['filepath'])[0])

    return JsonResponse(filtered_results['response']['docs'], safe=False)


def kb_search_tags_booktitles(request):

    conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))

    term = escape_solr_terms(handle_quotes(request, request.GET['term']))

    solr_args = {'q': '(tags:{}* OR (doctype:book AND title:*{}*)) AND user_id:{}'.format(term, term, request.user.id),
                 'fl': 'doctype,filepath,sha1sum,tags,title,uuid',
                 'rows': 20}

    results = json.loads(conn.raw_query(**solr_args).decode('UTF-8'))

    tags = {}
    matches = []

    for match in results['response']['docs']:
        if match['doctype'] == 'book':
            matches.append({'type': 'Book', 'value': match['title'][0], 'uuid': match.get('uuid')})
        if match.get('tags', ''):
            for tag in [x for x in match['tags'] if x.lower().startswith(term.lower())]:
                tags[tag] = 1

    for tag in tags:
        matches.append({'type': 'Tag', 'value': tag})

    return JsonResponse(matches, safe=False)


def escape_solr_terms(term):
    """Escape special characters used by Solr with a backslash"""
    return re.sub(r"([:\[\]\{\}\(\)])", r"\\\1", term)


def handle_quotes(request, search_term):
    """Remove quotes to avoid Solr errors. Support the 'Exact Match' search option."""
    search_term = search_term.replace("\"", "")
    if request.GET.get('exact_match'):
        search_term = "\"{}\"".format(search_term)
    return search_term


@login_required
def search_admin(request):

    # Get some document count stats.  Any way to do this with just one query?
    stats = {}

    conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
    for doctype in ['blob', 'bordercore_blog', 'book', 'bordercore_todo', 'bordercore_bookmark', 'document']:
        solr_args = {'q': 'doctype:{}'.format(doctype), 'rows': 1}
        r = json.loads(conn.raw_query(**solr_args).decode('UTF-8'))
        stats[doctype] = r['response']['numFound']

    if request.method == 'POST':

        if request.POST['Go'] in ['Delete']:
            conn.delete_query('doctype:%s' % request.POST['doc_type'])
            conn.commit()
        elif request.POST['Go'] in ['Commit']:
            conn.commit()

    return render(request, 'kb/admin.html',
                  {'stats': stats})
