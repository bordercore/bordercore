import datetime
import json
import os
import re

from django.conf import settings
from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from amazonproduct import API
from amazonproduct.errors import NoExactMatchesFound
from blob.forms import DocumentForm
from blob.models import Document, MetaData
from blob.tasks import index_blob
from collection.models import Collection

SECTION = 'Blob'

# TODO: Move this to Django config file
amazon_api_config = {
}


class DocumentCreateView(CreateView):
    template_name = 'blob/edit.html'
    form_class = DocumentForm

    def get_context_data(self, **kwargs):
        context = super(DocumentCreateView, self).get_context_data(**kwargs)
        context['action'] = 'Add'
        if self.request.GET.get('linked_blob', ''):
            linked_blob = Document.objects.get(id=self.request.GET['linked_blob'])
            context['linked_blob'] = linked_blob
            # Grab the initial metadata from the linked blob
            context['metadata'] = linked_blob.metadata_set.all()
        if self.request.GET.get('linked_collection', ''):
            collection_id = self.request.GET['linked_collection']
            context['linked_collection_info'] = Collection.objects.get(id=collection_id)
            context['linked_collection_blob_list'] = [Document.objects.get(pk=x['id']) for x in Collection.objects.get(id=collection_id).blob_list]
            # Grab the initial metadata from one of the other blobs in the collection
            context['metadata'] = context['linked_collection_blob_list'][0].metadata_set.all()
        return context

    def get_form(self, form_class=None):
        form = super(DocumentCreateView, self).get_form(form_class)

        if self.request.GET.get('is_blog', False):
            form.initial['is_blog'] = True
        if self.request.GET.get('linked_blob', False):
            blob = Document.objects.get(pk=int(self.request.GET.get('linked_blob')))
            form.initial['tags'] = ','.join([x.name for x in blob.tags.all()])
            form.initial['date'] = blob.date
            form.initial['title'] = blob.title
        if self.request.GET.get('linked_collection', False):
            collection_id = self.request.GET['linked_collection']
            blob_id = Collection.objects.get(id=collection_id).blob_list[0]['id']
            blob = Document.objects.get(pk=blob_id)
            form.initial['tags'] = ','.join([x.name for x in blob.tags.all()])
            form.initial['date'] = blob.date
            form.initial['title'] = blob.title

        return form

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()

        # Take care of the tags.  Create any that are new.
        for tag in form.cleaned_data['tags']:
            obj.tags.add(tag)

        obj.save()

        handle_metadata(obj, self.request)

        handle_linked_blob(obj, self.request)

        handle_linked_collection(obj, self.request)

        index_blob.delay(obj.uuid, True)

        return super(DocumentCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blob_detail', kwargs={'uuid': self.object.uuid})


class BlobDeleteView(DeleteView):
    model = Document
    success_url = reverse_lazy('blob_add')

    def get_object(self, queryset=None):
        obj = Document.objects.get(user=self.request.user, uuid=self.kwargs.get('uuid'))
        return obj


class BlobDetailView(DetailView):

    model = Document
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    # When we rename the object, we should be able to remove this and let
    # Django figure out the template name on its own
    template_name = 'blob/blob_detail.html'

    def get_context_data(self, **kwargs):
        context = super(BlobDetailView, self).get_context_data(**kwargs)
        context['id'] = self.object.id
        context['metadata'] = {}
        for x in self.object.metadata_set.all():
            if x.name == 'Url':
                try:
                    context['metadata'][x.name].append(x.value)
                except KeyError:
                    context['metadata'][x.name] = [x.value]
            else:
                if context['metadata'].get(x.name, ''):
                    context['metadata'][x.name] = ', '.join([context['metadata'][x.name], x.value])
                else:
                    context['metadata'][x.name] = x.value

        from lib.time_utils import get_date_from_pattern
        context['date'] = get_date_from_pattern(self.object.date)

        if self.object.sha1sum:
            context['cover_info'] = Document.get_cover_info(self.object.sha1sum)
            context['cover_info_small'] = Document.get_cover_info(self.object.sha1sum, 'small')
        try:
            query = 'uuid:%s' % self.object.uuid
            context['solr_info'] = self.object.get_solr_info(query)['docs'][0]
            if context['solr_info'].get('content_type', ''):
                context['content_type'] = self.object.get_content_type(context['solr_info']['content_type'][0])
        except IndexError:
            # Give Solr up to a minute to index the blob
            if int(datetime.datetime.now().strftime("%s")) - int(self.object.created.strftime("%s")) < 60:
                messages.add_message(self.request, messages.INFO, 'New blob not yet indexed in Solr')
            else:
                messages.add_message(self.request, messages.ERROR, 'Blob not found in Solr')
        context['title'] = self.object.get_title(remove_edition_string=True)
        context['fields_ignore'] = ['is_book', 'Url', 'Publication Date', 'Title', 'Author']

        context['current_collections'] = Collection.objects.filter(blob_list__contains=[{'id': self.object.id}])

        collection_info = []

        for collection in Collection.objects.filter(blob_list__contains=[{'id': self.object.id}]):
            blob_list = Document.objects.filter(pk__in=[x['id'] for x in collection.blob_list if x['id'] != self.object.id])
            collection_info.append({'id': collection.id,
                                    'name': collection.name,
                                    'is_private': collection.is_private,
                                    'blob_list': blob_list})
        context['collection_info'] = collection_info
        return context


class BlobUpdateView(UpdateView):
    template_name = 'blob/edit.html'
    form_class = DocumentForm

    def get_context_data(self, **kwargs):
        context = super(BlobUpdateView, self).get_context_data(**kwargs)
        context['section'] = SECTION
        context['sha1sum'] = self.kwargs.get('sha1sum')
        context['cover_info'] = Document.get_cover_info(self.object.sha1sum, max_cover_image_width=400)
        context['metadata'] = [x for x in self.object.metadata_set.all() if x.name != 'is_book']
        if True in [True for x in self.object.metadata_set.all() if x.name == 'is_book']:
            context['is_book'] = True
        context['collections_other'] = Collection.objects.filter(Q(user=self.request.user)
                                                                 & ~Q(blob_list__contains=[{'id': self.object.id}])
                                                                 & Q(is_private=False))
        context['action'] = 'Edit'
        return context

    def get(self, request, **kwargs):
        self.object = Document.objects.get(user=self.request.user, uuid=self.kwargs.get('uuid'))
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        context = self.get_context_data(object=self.object, form=form)
        return render(request, self.template_name, context)

    def get_object(self, queryset=None):
        obj = Document.objects.get(user=self.request.user, uuid=self.kwargs.get('uuid'))
        return obj

    def form_valid(self, form):
        blob = form.instance

        file_changed = False if 'file' not in form.changed_data else True

        # Only check for a renamed file if the file itself hasn't changed
        if not file_changed:
            import os
            old_filename = str(form.instance.file)
            if (form.cleaned_data['filename'] != os.path.basename(old_filename)):
                new_file_path = '{}/{}/{}'.format(settings.MEDIA_ROOT, os.path.dirname(old_filename), form.cleaned_data['filename'])
                try:
                    os.rename(blob.file.path, new_file_path)
                    blob.file.name = "{}/{}".format(os.path.dirname(str(form.instance.file)), form.cleaned_data['filename'])
                    blob.save()
                except Exception as e:
                    from django.forms import ValidationError
                    raise ValidationError("Error: {}".format(e))

        # Delete all existing tags
        blob.tags.clear()

        handle_metadata(blob, self.request)

        self.object = form.save()
        messages.add_message(self.request, messages.INFO, 'Blob updated')
        index_blob.delay(blob.uuid, file_changed)

        return HttpResponseRedirect(reverse('blob_detail', kwargs={'uuid': str(blob.uuid)}))


class BlobThumbnailView(UpdateView):
    template_name = 'blob/thumbnail.html'
    form_class = DocumentForm

    def get_context_data(self, **kwargs):
        context = super(BlobThumbnailView, self).get_context_data(**kwargs)
        context['cover_info'] = Document.get_cover_info(self.object.sha1sum, max_cover_image_width=70, size='small')
        context['filename'] = self.object.file
        query = 'uuid:{}'.format(self.object.uuid)
        context['solr_info'] = self.object.get_solr_info(query)['docs'][0]
        if context['solr_info'].get('content_type', ''):
            context['content_type'] = self.object.get_content_type(context['solr_info']['content_type'][0]).lower()

        return context

    def get_object(self, queryset=None):
        obj = Document.objects.get(user=self.request.user, uuid=self.kwargs.get('uuid'))
        return obj


# Metadata objects are not handled by the form -- handle them manually
def handle_metadata(blob, request):
    metadata = json.loads(request.POST['metadata'])

    # Delete all existing metadata
    blob.metadata_set.all().delete()

    for m in metadata:
        new_metadata, created = MetaData.objects.get_or_create(name=m[0], value=m[1], blob=blob)
        if created:
            new_metadata.save()
    if request.POST.get('is_book', ''):
        new_metadata = MetaData(name='is_book', value='true', blob=blob)
        new_metadata.save()


def handle_linked_blob(blob, request):

    if request.POST.get('linked_blob', ''):
        blob_list = [{'id': int(request.POST['linked_blob']), 'added': int(datetime.datetime.now().strftime("%s"))},
                     {'id': blob.id, 'added': int(datetime.datetime.now().strftime("%s"))}]
        collection = Collection(blob_list=blob_list, user=request.user, is_private=True)
        collection.save()


def handle_linked_collection(blob, request):

    if request.POST.get('linked_collection', ''):
        collection = Collection.objects.get(user=request.user, id=int(request.POST['linked_collection']))
        blob = {'id': blob.id, 'added': int(datetime.datetime.now().strftime("%s"))}
        collection.blob_list.append(blob)
        collection.save()


def metadata_name_search(request):

    m = MetaData.objects.all().values('name').filter(name__icontains=request.GET['query']).distinct('name').order_by('name'.lower())

    return_data = [{'value': x['name']} for x in m]

    return JsonResponse(return_data, safe=False)


def get_amazon_image_info(request, sha1sum, index=0):

    b = Document.objects.get(sha1sum=sha1sum)
    result = b.get_amazon_cover_url(int(index))

    return JsonResponse(result)


def set_amazon_image_info(request, sha1sum, index=0):

    b = Document.objects.get(sha1sum=sha1sum)
    try:
        b.set_amazon_cover_url('small', request.POST['small'])
        b.set_amazon_cover_url('large', request.POST['large'])
        result = {'message': 'Cover image updated'}
    except Exception as e:
        result = {'message': str(e), 'error': True}

    return JsonResponse(result)


def amazon_metadata_dupe_check(dupes, name, value):
    if value in dupes[name]:
        return False
    else:
        dupes[name][value] = True
        return True


def get_amazon_metadata(request, title):

    api = API(cfg=amazon_api_config)

    return_data = {'data': []}
    dupes = {'Title': {}, 'Author': {}, 'Publication Date': {}}

    try:
        results = api.item_search('Books', Title=title, ResponseGroup='Medium', Sort='-publication_date')
        for result in results:
            try:
                title = result.ItemAttributes.Title.text
                if amazon_metadata_dupe_check(dupes, 'Title', title):
                    return_data['data'].append(['Title', title])
                author_raw = result.ItemAttributes.Author.text
                matches = [x.strip() for x in re.split("\s?;\s?|\s?,\s?", author_raw)]
                for author in matches:
                    if amazon_metadata_dupe_check(dupes, 'Author', author):
                        return_data['data'].append(['Author', author])
                publication_data_raw = str(result.ItemAttributes.PublicationDate)
                matches = re.match(r'^(\d\d\d\d)', publication_data_raw)
                if matches:
                    publication_date = matches.group(1)
                else:
                    publication_date = str(result.ItemAttributes.PublicationDate)
                if amazon_metadata_dupe_check(dupes, 'Publication Date', publication_date):
                    return_data['data'].append(['Publication Date', publication_date])
            except AttributeError as e:
                print("AttributeError: %s" % e)
    except NoExactMatchesFound:
        return_data['error'] = "No Amazon matches found"

    return JsonResponse(return_data)


def extract_thumbnail_from_pdf(request, uuid, page_number):
    from PyPDF2 import PdfFileReader, PdfFileWriter

    page_number = int(page_number) - 1

    b = Document.objects.get(uuid=uuid)

    os.chdir("{}/{}".format(settings.MEDIA_ROOT, os.path.dirname(b.file.name)))

    # Ex: d7/d77d08dd2e51680229adbf175101b8f65f3717fc/Comprehensive Report.pdf
    input_file = os.path.basename(b.file.name)

    # Ex: Comprehensive Report_p1.pdf
    outfile = "{}_p{}.pdf".format(os.path.splitext(input_file)[0], page_number)

    input_pdf = PdfFileReader(open(input_file, "rb"))

    output = PdfFileWriter()
    output.addPage(input_pdf.getPage(page_number))
    outputStream = open(outfile, "wb")
    output.write(outputStream)
    outputStream.close()

    # Convert the pdf page to jpg
    from pdf2image import convert_from_path
    pages = convert_from_path(outfile, dpi=150)
    cover_large = "cover-large.jpg"
    pages[0].save(cover_large, "JPEG")

    # Create small (thumbnail) jpg
    from PIL import Image

    size = 128, 128

    try:
        im = Image.open(cover_large)
        im.thumbnail(size)
        im.save("cover-small.jpg".format(page_number), "JPEG")
    except IOError:
        print("Cannot create thumbnail for {}".format(cover_large))

    os.remove(outfile)

    cover_info = Document.get_cover_info(b.sha1sum, max_cover_image_width=70, size='small')

    return JsonResponse({'message': 'OK', 'cover_url': cover_info['url']})


def collection_mutate(request):

    blob_id = int(request.POST['blob_id'])
    collection = Collection.objects.get(user=request.user, id=int(request.POST['collection_id']))
    mutation = request.POST['mutation']

    message = ''

    if mutation == 'add':
        blob = {'id': blob_id, 'added': int(datetime.datetime.now().strftime("%s"))}
        if collection.blob_list:
            if [x for x in collection.blob_list if x['id'] == blob_id]:
                message = 'Blob already in collection'
            else:
                collection.blob_list.append(blob)
        else:
            collection.blob_list = [blob]
        message = 'Added to collection'
    elif mutation == 'delete':
        collection.blob_list = [x for x in collection.blob_list if x['id'] != blob_id]
        message = 'Deleted from collection'

    collection.save()

    return JsonResponse({'message': message})


class BlogListView(ListView):
    model = Document
    template_name = "blob/blog_list.html"
    ITEMS_PER_PAGE = 10
    SECTION = 'Blog'

    def get_queryset(self):
        if self.request.GET.get('tagsearch', ''):
            post_list = Document.objects.filter(tags__name__exact=self.request.GET['tagsearch']).filter(is_blog=True).order_by('-created')
        elif 'search_item' in self.request.GET:
            post_list = Document.objects.filter(
                (Q(content__icontains=self.request.GET['search_item']) |
                 Q(title__icontains=self.request.GET['search_item'])) &
                Q(is_blog=True)
            )
        else:
            post_list = Document.objects.order_by('-created').filter(is_blog=True)

        paginator = Paginator(post_list, self.ITEMS_PER_PAGE)

        page = self.request.GET.get('page')
        try:
            posts = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            posts = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            posts = paginator.page(paginator.num_pages)

        return posts

    def get_context_data(self, **kwargs):
        context = super(BlogListView, self).get_context_data(**kwargs)

        if not self.object_list.paginator.page(1).object_list:
            messages.add_message(self.request, messages.ERROR, 'No blog entries found')

        context['section'] = self.SECTION
        return context
