from django.views.generic.list import ListView
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.template import RequestContext

import json
import os
from os.path import basename
import solr
import urllib

from tag.models import Tag

SOLR_HOST = 'localhost'
SOLR_PORT = 8080
SOLR_COLLECTION = 'solr/bordercore'


class SearchListView(ListView):

    template_name = 'kb/search/index.html'
    SOLR_COUNT_PER_PAGE = 100
    context_object_name = 'info'

    def get_facet_query(self, facet, term):

        if facet == 'Books':
            return 'doctype:book'
        elif facet == 'Documents':
            return 'doctype:document'
        elif facet == 'Todos':
            return 'doctype:bordercore_todo'
        elif facet == 'Blog Posts':
            return 'doctype:bordercore_blog'
        elif facet == 'Links':
            return 'doctype:bordercore_bookmark'
        elif facet == 'Book Titles':
            return '(doctype:book AND title:%s)' % (term)
        elif facet == 'Tags':
            return 'tags:%s' % (term)

    def get_queryset(self):

        if 'search' in self.request.GET:

            search_term = self.request.GET['search']
            rows = self.request.GET['rows']
            if rows == 'No limit':
                rows = 1000000
            elif rows is None:
                rows = self.SOLR_COUNT_PER_PAGE

            # TODO: catch SolrException
            conn = solr.SolrConnection('http://%s:%d/%s' % (SOLR_HOST, SOLR_PORT, SOLR_COLLECTION) )

            solr_args = { 'q': 'title:%s attr_content:%s bordercore_todo_task:%s tags:%s bordercore_bookmark_title:%s' % (search_term, search_term, search_term, search_term, search_term),
                          'rows': rows,
                          'facet': 'on',
                          'facet.mincount': '1',
                          'fields': ['attr_*','author','doctype','filepath','tags','title','author', 'url'],
                          'wt': 'json',
                          'fl': 'author,bordercore_todo_task,bordercore_bookmark_title,doctype,filepath,id,internal_id,last_modified,tags,title,url,bordercore_blogpost_title,attr_publication_date',
                          'hl': 'true',
                          'hl.fl': 'attr_content,bordercore_todo_task,bordercore_bookmark_title,title',
                          'hl.simple.pre': '<span class="search_bordercore_blogpost_snippet">',
                          'hl.simple.post': '</span>'}

            facet_queries = []
            for facet in ['Blog Posts', 'Books', 'Book Titles', 'Documents', 'Links', 'Tags', 'Todos']:
                facet_queries.append( '{!key="%s" ex=dt}' % (facet) + self.get_facet_query(facet, search_term) )
            solr_args['facet.query'] = facet_queries

            if self.request.GET.get('facets'):
                solr_args['fq'] = '{!tag=dt}' + ' OR '.join([self.get_facet_query(x, search_term) for x in self.request.GET.get('facets').split(',')])

            results = conn.raw_query(**solr_args)
            return json.loads(results)

    def get_context_data(self, **kwargs):
        context = super(SearchListView, self).get_context_data(**kwargs)

        info = []
        facet_counts = {}

        if self.request.GET.get('facets'):
            context['filter_query'] = self.request.GET.get('facets').split(',')

        from solr.core import utc_from_string
        from lib.time_utils import pretty_date

        if context['info']:

            for k, v in context['info']['facet_counts']['facet_queries'].iteritems():
                if v > 0:
                    facet_counts[k] = v

            for myobject in context['info']['response']['docs']:
                filename = ''
                last_modified = ''
                blogpost_snippet = ''
                # TODO: Handle matches with multiple titles
                if myobject.get('last_modified'):
                    last_modified = pretty_date(utc_from_string(myobject.get('last_modified')))
                if myobject.get('filepath'):
                    filename = os.path.basename(myobject['filepath'])
                if myobject['doctype'] == 'book' and not myobject.get('title', ''):
                    myobject['title'] = filename
                if myobject['doctype'] == 'bordercore_blog':
                    if context['info']['highlighting'][ myobject['id'] ].get('attr_content'):
                        blogpost_snippet = context['info']['highlighting'][ myobject['id'] ]['attr_content'][0]
                info.append( dict(title=get_title(myobject),
                                  author=myobject.get('author','no author'),
                                  pub_date=myobject.get('attr_publication_date',''),
                                  doctype=myobject['doctype'],
                                  id=myobject['id'],
                                  internal_id=myobject.get('internal_id', ''),
                                  last_modified=last_modified,
                                  url=myobject.get('url', ''),
                                  filename=filename,
                                  tags=myobject.get('tags'),
                                  bordercore_todo_task=myobject.get('bordercore_todo_task',''),
                                  bordercore_blogpost_title=myobject.get('bordercore_blogpost_title',''),
                                  blogpost_snippet = blogpost_snippet,
                                  bordercore_bookmark_title=myobject.get('bordercore_bookmark_title',''),
 ) )
            context['numFound'] = context['info']['response']['numFound']

            # Convert to a list of dicts.  This lets us use the dictsortreversed
            #  filter in our template to sort by count.
            context['facet_counts'] = [{'doctype_purty': k, 'doctype': k, 'count': v } for k, v in facet_counts.iteritems()]

        context['info'] = info
        return context


class SearchTagDetailView(ListView):

    template_name = 'kb/search/tag_detail.html'
    SOLR_COUNT_PER_PAGE = 100
    context_object_name = 'info'

    def get_context_data(self, **kwargs):
        context = super(SearchTagDetailView, self).get_context_data(**kwargs)
        results = {}
        for one_doc in context['info']['response']['docs']:
            if one_doc['doctype'] == 'book':
                one_doc['filename'] = os.path.basename(one_doc['filepath'])
            if results.get(one_doc['doctype'], ''):
                results[one_doc['doctype']].append(one_doc)
            else:
                results[one_doc['doctype']] = [ one_doc ]
        context['info']['matches'] = results

        tag_counts = {}
        tag_list = self.kwargs['taglist'].split(',')
        for x, y in grouped(context['info']['facet_counts']['facet_fields']['tags'], 2):
            if x not in tag_list:
                tag_counts[x] = y
        doctype_counts = {}
        for x, y in grouped(context['info']['facet_counts']['facet_fields']['doctype'], 2):
            if x not in tag_list:
                doctype_counts[x] = y

        meta_tags = [x for x in tag_counts if x in Tag.get_meta_tags()]
        context['meta_tags'] = meta_tags

        import operator
        tag_counts_sorted = sorted(tag_counts.items(), key=operator.itemgetter(1), reverse=True)
        context['tag_counts'] = tag_counts_sorted
        doctype_counts_sorted = sorted(doctype_counts.items(), key=operator.itemgetter(1), reverse=True)
        context['doctype_counts'] = doctype_counts_sorted

        tag_list_js = []
        for tag in tag_list:
            if tag != '':
                tag_list_js.append( {'name': tag, 'is_meta': 'true' if tag in Tag.get_meta_tags() else 'false'} )
        context['tag_list'] = tag_list_js

        return context

    def get_queryset(self):
        taglist = self.kwargs['taglist']
        rows = 1000

        q = ' AND '.join([ 'tags:"%s"' % (urllib.unquote(t).decode('utf8'),) for t in taglist.split(',') ])

        conn = solr.SolrConnection('http://%s:%d/%s' % (SOLR_HOST, SOLR_PORT, SOLR_COLLECTION) )

        solr_args = { 'q': q,
                      'rows': rows,
                      'fields': ['attr_*','author','doctype','filepath','tags','title','author', 'url'],
                      'wt': 'json',
                      'fl': 'author,bordercore_todo_task,bordercore_bookmark_title,doctype,filepath,id,internal_id,last_modified,tags,title,url,bordercore_blogpost_title',
                      'facet': 'on',
                      'facet.mincount': '1',
                      'facet.field': ['{!ex=tags}tags','{!ex=doctype}doctype'],
                      'sort': 'last_modified+desc'
        }

        results = conn.raw_query(**solr_args)
        return json.loads(results)


from itertools import izip

def grouped(iterable, n):
    "s -> (s0,s1,s2,...sn-1), (sn,sn+1,sn+2,...s2n-1), (s2n,s2n+1,s2n+2,...s3n-1), ..."
    return izip(*[iter(iterable)]*n)


def get_title(myobject):

    title = myobject.get('title')
    if not title:
        title = '<no title>'
    elif title == 'untitled':
        # Use the filename (minus the extension) as the title
        import re
        p = re.compile('^(.*/)?(?:$|(.+?)(?:(\.[^.]*$)|$))')
        m = p.match(myobject['filepath'])
        if m:
            title = m.group(2)
    return title


@login_required
def search_book_title(request):

    conn = solr.SolrConnection('http://%s:%d/%s' % (SOLR_HOST, SOLR_PORT, SOLR_COLLECTION) )

    title = request.GET['title']

    solr_args = { 'q': 'doctype:book AND filepath:*%s*' % title,
                  'fl': 'id,score,title,author,filepath',
                  'wt': 'json' }

    results = conn.raw_query(**solr_args)

    filtered_results = json.loads(results)

    for match in filtered_results['response']['docs']:
        # If the book doesn't have a title, use the filename
        match['filename'] = os.path.basename(match.get('filepath'))
        if not match.get('title'):
            match['title'] = basename(os.path.splitext(match['filepath'])[0])

    return render_to_response('return_json.json',
                              { 'info': json.dumps(filtered_results['response']['docs']) },
                              content_type="application/json",
                              context_instance=RequestContext(request))


def kb_search_tags_booktitles(request):

    conn = solr.SolrConnection('http://%s:%d/%s' % (SOLR_HOST, SOLR_PORT, SOLR_COLLECTION) )

    term = request.GET['term']

    solr_args = { 'q': 'tags:%s* OR (doctype:book AND title:*%s*)' % (term, term),
                  'fl': 'doctype,filepath,tags,title',
                  'wt': 'json' }

    results = json.loads(conn.raw_query(**solr_args))

    tags = {}
    matches = []

    for match in results['response']['docs']:
        if match['doctype'] == 'book':
            matches.append({'type': 'Book', 'value': match['title'], 'filename': os.path.basename(match.get('filepath'))})
        if match.get('tags', ''):
            print match['tags']
            for tag in [x for x in match['tags'] if x.lower().startswith(term.lower())]:
                tags[tag] = 1

    for tag in tags:
        matches.append({'type': 'Tag', 'value': tag})

    return render_to_response('return_json.json',
                              { 'info': json.dumps(matches) },
                              content_type="application/json",
                              context_instance=RequestContext(request))


def search_document_source(request):

    conn = solr.SolrConnection('http://%s:%d/%s' % (SOLR_HOST, SOLR_PORT, SOLR_COLLECTION) )

    doc_source = request.GET['doc_source']

    solr_args = { 'q': 'doctype:document AND source:*%s*' % doc_source,
                  'fl': 'id,source',
                  'wt': 'json',
                  'group': 'true',
                  'group.field': 'source'
              }

    results = json.loads(conn.raw_query(**solr_args))

    return_data = []

    for match in results['grouped']['source']['groups']:
        return_data.append( {'source': match['doclist']['docs'][0]['source'] } )

    return render_to_response('return_json.json',
                              { 'info': json.dumps(sorted(return_data)) },
                              content_type="application/json",
                              context_instance=RequestContext(request))


@login_required
def search_admin(request):

    # Get some document count stats.  Any way to do this with just one query?
    stats = {}

    conn = solr.SolrConnection('http://%s:%d/%s' % (SOLR_HOST, SOLR_PORT, SOLR_COLLECTION) )
    for doctype in ['book', 'bordercore_todo', 'bordercore_bookmark']:
        r = conn.query('doctype:%s' % doctype, rows=1)
        stats[doctype] = r.numFound

    if request.method == 'POST':

        if request.POST['Go'] in ['Delete']:
            print request.POST['doc_type']

            conn = solr.SolrConnection('http://%s:%d/%s' % (SOLR_HOST, SOLR_PORT, SOLR_COLLECTION) )
            conn.delete_query('doctype:%s' % request.POST['doc_type'])
            conn.commit()
        elif request.POST['Go'] in ['Commit']:

            conn = solr.SolrConnection('http://%s:%d/%s' % (SOLR_HOST, SOLR_PORT, SOLR_COLLECTION) )
            conn.commit()


    return render_to_response('search/admin.html',
                              { 'stats': stats },
                              context_instance=RequestContext(request))
