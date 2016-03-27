from django.conf import settings
from django.http import HttpResponse
from django.templatetags.static import static
from django.views.generic.list import ListView

from bookshelf.models import Bookshelf

from blob.models import Blob

import json
import os
import solr

IMAGE_TYPE_LIST = ['jpeg', 'gif', 'png']


class BookshelfListView(ListView):

    model = Bookshelf
    template_name = 'bookshelf/bookshelf_list.html'

    def get_queryset(self):

        book_shelves = Bookshelf.objects.filter(user=self.request.user, blob_list__isnull=False)

        blob_list = {}

        for shelf in book_shelves:
            q = 'id:(%s)' % ' '.join(['"blob_%s"' % t for t in shelf.blob_list])

            conn = solr.SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))

            solr_args = {'q': q,
                         'rows': 1000,
                         'fields': ['attr_*', 'author', 'content_type', 'doctype', 'filepath', 'tags', 'title', 'author', 'url'],
                         'wt': 'json',
                         'fl': 'author,bordercore_todo_task,bordercore_bookmark_title,content_type,doctype,filepath,id,internal_id,attr_is_book,last_modified,tags,title,sha1sum,url,bordercore_blogpost_title'
            }

            results = conn.raw_query(**solr_args)

            # Build a temporary dict for fast lookup
            solr_list_objects = {}
            for x in json.loads(results)['response']['docs']:
                solr_list_objects[int(x['id'].split('blob_')[1])] = x

            # Solr doesn't return the blobs in the order specified in postgres, so we need to re-order
            blob_list_temp = []
            for blob in shelf.blob_list:
                try:
                    blob_list_temp.append(solr_list_objects[blob])
                except KeyError:
                    print "Warning: blob_id = %s not found in solr.  It's probably new." % blob
            blob_list[shelf.id] = {'blob_list': blob_list_temp, 'name': shelf.name}

        return blob_list

    def get_context_data(self, **kwargs):
        context = super(BookshelfListView, self).get_context_data(**kwargs)

        for id, value in context['object_list'].iteritems():
            for object in value['blob_list']:
                if object['doctype'] in ('blob', 'book'):
                    filename = os.path.basename(object['filepath'])
                    object['url'] = object['filepath'].split(Blob.BLOB_STORE)[1]
                    object['cover_url'] = static("blobs/%s/%s/cover-small.jpg" % (object['sha1sum'][0:2], object['sha1sum']))
                    if not os.path.isfile("%s/%s/%s/cover-small.jpg" % (Blob.BLOB_STORE, object['sha1sum'][0:2], object['sha1sum'])):
                        object['cover_url'] = static("images/book.png")
                    if object['content_type']:
                        object['content_type'] = object['content_type'][0].split('/')[1]
                        if object['content_type'] in IMAGE_TYPE_LIST:
                            object['is_image'] = True
                    if not object.get('title', ''):
                        object['title'] = filename

        return context


def sort_bookshelf(request):

    blob_id = int(request.POST['blob_id'])
    new_position = int(request.POST['position'])

    b = Bookshelf.objects.get(user=request.user)

    # First remove the blob from the existing list
    b.blob_list[0]['blobs'].remove(blob_id)

    # Then re-insert it in its new position
    b.blob_list[0]['blobs'].insert(new_position - 1, blob_id)

    b.save()

    return HttpResponse(json.dumps('OK'), content_type="application/json")


def add_to_bookshelf(request):

    blob_id = int(request.POST['blob_id'])
    shelf_id = int(request.POST['shelf_id'])
    b = Bookshelf.objects.filter(user=request.user, id=shelf_id)

    message = ''
    for shelf in b:
        if shelf.blob_list:
            if blob_id not in shelf.blob_list:
                shelf.blob_list.append(blob_id)
                shelf.save()
                message = 'Added to bookshelf'
            else:
                message = 'Already on bookshelf'
        else:
            shelf.blob_list = [blob_id]
            shelf.save()

    response = json.dumps({"message": message})
    return HttpResponse(response, content_type="application/json")


def remove_from_bookshelf(request):

    blob_id = int(request.POST['blob_id'])
    shelf_id = int(request.POST['shelf_id'])
    b = Bookshelf.objects.get(user=request.user, id=shelf_id)

    try:
        b.blob_list.remove(blob_id)
        b.save()
        message = 'Removed from bookshelf'
    except ValueError:
        message = 'Not on bookshelf'

    response = json.dumps({"message": message})
    return HttpResponse(response, content_type="application/json")
