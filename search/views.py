from django.views.generic.list import ListView
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.template import RequestContext

import json
import os
from os.path import basename
import solr

SOLR_HOST = 'localhost'
SOLR_PORT = 8080
SOLR_COLLECTION = 'solr/bordercore'


class SearchListView(ListView):

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

    template_name = 'search/index.html'
    SOLR_COUNT_PER_PAGE = 100
    context_object_name = 'info'

    def get_queryset(self):

        if 'search' in self.request.GET:

            search_term = self.request.GET['search']
            rows = 100
            # rows = self.request.GET['rows']
            # if rows == 'No limit':
            #     rows = 1000000
            # elif rows is None:
            #     rows = self.SOLR_COUNT_PER_PAGE

            # TODO: catch SolrException
            conn = solr.SolrConnection('http://%s:%d/%s' % (SOLR_HOST, SOLR_PORT, SOLR_COLLECTION) )

            solr_args = { 'q': 'title:%s attr_content:%s bordercore_todo_task:%s tags:%s' % (search_term, search_term, search_term, search_term),
                          'rows': rows,
                          'facet': 'on',
                          'facet.mincount': '1',
                          'fields': ['attr_*','doctype','filepath','tags','title','author', 'url'],
                          'wt': 'json',
                          'fl': 'author,bordercore_todo_task,bordercore_bookmark_title,doctype,filepath,id,last_modified,tags,title,url,bordercore_blogpost_title',
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

        if context['info']['response']:

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
                                  doctype=myobject['doctype'],
                                  id=myobject['id'],
                                  last_modified=last_modified,
                                  url=myobject.get('url', ''),
                                  filename=filename,
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
