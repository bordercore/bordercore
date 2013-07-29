import errno
import hashlib
import os
from os import makedirs
from os.path import isfile
import re
from shutil import move
import time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.forms.util import ErrorList
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from django_datatables_view.base_datatable_view import BaseDatatableView
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

from music.models import Album, Listen, Song, WishList
from music.forms import SongForm, WishListForm

SECTION = 'Music'
MUSIC_ROOT = "/home/media/music"

@login_required
def music_list(request):

    message = ''

    # Get a list of recently played songs
    recent_songs = Song.objects.all().order_by('-created')[:5]

    # Get a random album
    random_albums = Album.objects.order_by('?')[0]

    return render_to_response('music/index.html',
                              {
            'section': SECTION,
            'cols': ['Date', 'artist', 'title', 'id'],
            'message': message,
            'recent_songs': recent_songs,
            'random_albums': random_albums
            },
                              context_instance=RequestContext(request))

@login_required
def music_stream(request, song_id):

    print "stream song %d" % int(song_id)

    song = Song.objects.get(id=song_id)

    # Increment the 'times played' counter
    if song.times_played:
        song.times_played = song.times_played + 1
    else:
        song.times_played = 1
    song.save()

    # Add this song to the listen table
    l = Listen(song=song, user=request.user)
    l.save()

    if song.album:
        tracknumber = str(song.track)
        if len(tracknumber) == 1:
            tracknumber = '0' + tracknumber
        file_path = "%s/%s/%s/%s - %s.mp3" % (MUSIC_ROOT, song.artist, song.album.title, tracknumber, song.title)
    else:
        file_path = "%s/%s/%s.mp3" % (MUSIC_ROOT, song.artist, song.title)

    from django.core.servers.basehttp import FileWrapper
    wrapper = FileWrapper(file(file_path))

    try:
#        fsock = open(file_path, "r")
#        response = HttpResponse( fsock, mimetype='audio/mpeg' )
        response = HttpResponse(wrapper, content_type='audio/mpeg', mimetype='audio/mpeg')
        response['Content-Length'] = os.path.getsize(file_path)

    except IOError:
        response = HttpResponseNotFound()

    return response


@login_required
def album_artwork(request, song_id):

    if len(song_id) == 32:
        file_path = "/tmp/%s" % song_id
    else:
        song = Song.objects.get(id=song_id)

        if not song.album:
            return HttpResponseNotFound()

        tracknumber = str(song.track)
        if len(tracknumber) == 1:
            tracknumber = '0' + tracknumber

            file_path = "%s/%s/%s/%s - %s.mp3" % (MUSIC_ROOT, song.artist, song.album.title, tracknumber, song.title)

    audio = MP3(file_path)
    artwork = audio.tags.get('APIC:')

    if artwork:
        return HttpResponse( artwork.data, mimetype=artwork.mime )
    else:
        return redirect("https://www.bordercore.com/static/img/image_not_found.jpg")


@login_required
def song_edit(request, song_id = None):

    action = 'Edit'
    file_info = None

    song = Song.objects.get(pk=song_id) if song_id else None

    tracknumber = str(song.track)
    if len(tracknumber) == 1:
        tracknumber = '0' + tracknumber

    if song.album:
        filename = "%s/%s/%s/%s - %s.mp3" % (MUSIC_ROOT, song.artist, song.album.title, tracknumber, song.title)
        try:
            id3_info = MP3(filename)
            file_info = { 'id3_info': id3_info,
                          'filesize': os.stat(filename).st_size,
                          'length': time.strftime('%M:%S', time.gmtime( id3_info.info.length )) }
        except IOError, e:
            messages.add_message(request, messages.ERROR, 'IOError: %s' % e)

    if request.method == 'POST':
        if request.POST['Go'] in ['Edit', 'Add']:
            form = SongForm(request.POST, instance=song) # A form bound to the POST data
            if form.is_valid():
                newform = form.save(commit=False)
                newform.user = request.user
                newform.save()
                form.save_m2m() # Save the many-to-many data for the form.
                messages.add_message(request, messages.INFO, 'Song edited')
                return music_list(request)
        elif request.POST['Go'] == 'Delete':
            song.delete()
            messages.add_message(request, messages.INFO, 'Song deleted')
            return music_list(request)

    elif song_id:
        action = 'Edit'
        form = SongForm(instance=song)

    else:
        action = 'Add'
        form = SongForm() # An unbound form

    return render_to_response('music/edit.html',
                              {'section': SECTION, 'action': action, 'form': form, 'file_info': file_info },
                              context_instance=RequestContext(request))


@login_required
def show_album(request, album_id):

    a = Album.objects.get(pk=album_id)
    s = Song.objects.filter(album=a).order_by('track')

    song_list = []

    for song in s:
        song_list.append( dict(id=song.id, track=song.track, title=song.title, length_seconds=song.length, length=time.strftime('%M:%S', time.gmtime(song.length))))

    return render_to_response('music/show_album.html',
                              {'section': SECTION, 'album': a, 'data': song_list,
                               'cols': ['id', 'track', 'title', 'length', 'length_seconds'] },
                              context_instance=RequestContext(request))


@login_required
def show_artist(request, artist_name):

    # Get all albums by this artist
    album_list = Album.objects.filter(artist=artist_name).order_by('-year')

    # Get all songs by this artist that do not appear on an album
    s = Song.objects.filter(artist=artist_name).filter(album__isnull=True)

    song_list = []

    for song in s:
        song_list.append( dict(id=song.id, date=song.created.strftime("%b %d, %Y"), title=song.title, artist=song.artist, info=song.comment))

    return render_to_response('music/show_artist.html',
                              {'section': SECTION, 'album_list': album_list, 'song_list': song_list, 'cols': ['date', 'artist', 'title', 'info', 'id'] },
                              context_instance=RequestContext(request))


@login_required
def add_song(request):

    info = {}
    notes = []
    md5sum = None
    form = None
    action = 'Upload'

    if 'upload' in request.POST:

        formdata = {}

        action = 'Review'
        blob = request.FILES['song'].read()
        md5sum = hashlib.md5(blob).hexdigest()
        filename = "/tmp/%s" % md5sum

        try:
            f = open(filename, "w")
            f.write(blob)
            f.close()
        except (IOError) as e:
            messages.add_message(request, messages.ERROR, 'IOError: %s' % e)

        info = MP3(filename, ID3=EasyID3)

        for field in ('artist', 'title', 'album'):
            formdata[ field ] = info[ field ][0] if info.get(field) else None
        if info.get('date'):
            formdata['year'] = info['date'][0]
        formdata['length'] = int(info.info.length)

        if info.get('album') and info.get('artist'):
            if info.get('album'):
                if Album.objects.filter(title=info['album'][0], artist=info['artist'][0]):
                    notes.append('You already have an album with this title')
                # Look for a fuzzy match
                fuzzy_matches = Album.objects.filter(Q(title__icontains='The Wait Is Over'.lower()))
                if fuzzy_matches:
                    notes.append('Found a fuzzy match on the album title: "%s" by %s' % (fuzzy_matches[0].title, fuzzy_matches[0].artist))

            if Song.objects.filter(title=info['title'][0], artist=info['artist'][0]):
                notes.append('You already have a song with this title by this artist')

        if info.get('tracknumber'):
            track_info = info['tracknumber'][0].split('/')
            track_number = track_info[0]
            formdata['track'] = track_number

        form = SongForm(initial=formdata)

        # This should initialize form._errors, used below
        form.full_clean()

        if formdata.get('year') and not re.search('^\d+$', formdata['year']):
            form._errors["year"] = ErrorList([u"Wrong format"])

    elif 'add' in request.POST:

        md5sum = request.POST['md5sum']

        if request.POST['year']:
            try:
                song = Song.objects.get(artist=request.POST['artist'], title=request.POST['title'], year=request.POST['year'])
            except ObjectDoesNotExist:
                song = None
        else:
            song = None

        form = SongForm(request.POST, instance=song) # A form bound to the POST data

        info = MP3("/tmp/%s" % md5sum, ID3=EasyID3)

        if form.is_valid():

            album_id = None

            # If an album was specified, check if we have the album
            if request.POST['album']:
                request.POST['album'] = request.POST['album'].strip()
                album_artist = form.cleaned_data['artist']
                if request.POST.get('compilation'):
                    album_artist = "Various Artists"
                try:
                    a = Album.objects.get(title=request.POST['album'], artist=album_artist)
                except ObjectDoesNotExist:
                    a = None
                if a:
                    if a.year != form.cleaned_data['year']:
                        messages.add_message(request, messages.ERROR, 'The same album exists but with a different year')
                else:
                    # This is a new album
                    a = Album(title=request.POST['album'],
                              artist=album_artist,
                              year=form.cleaned_data['year'],
                              compilation=request.POST.get('compilation', False))
            else:
                # No album was specified
                a = None

            if not messages.get_messages(request):
                if a:
                    a.save()
                form.cleaned_data['length'] = int(info.info.length)
                newform = form.save(commit=False)
                if a:
                    newform.album = a
                newform.save()

            if a:
                album_id = a.id

            # First create the directory structure, if necessary.
            # One directory for the artist and one for the album (if specified)
            fulldirname = MUSIC_ROOT
            if request.POST.get('compilation'):
                fulldirname = "%s/%s/%s" % (fulldirname, "Various Artists", request.POST['album'])
            else:
                fulldirname = "%s/%s" % (fulldirname, form.cleaned_data['artist'])
                if request.POST['album']:
                    fulldirname = "%s/%s" % (fulldirname, request.POST['album'])

            try:
                makedirs(fulldirname)
            except OSError, e:
                if not e.errno == errno.EEXIST:
                    raise OSError(e)

            # Move the song to the media drive
            if len(str(form.cleaned_data['track'])) == 1:
                form.cleaned_data['track'] = '0' + str(form.cleaned_data['track'])

            # For album tracks, we want to filename to be in this format:  <track> - <song>.mp3
            #   Check if the track number is already present
            filename = form.cleaned_data['title'] + '.mp3'
            if request.POST['album']:
                p = re.compile("^(\d+) - ")
                if not p.match(filename):
                    filename = "%s - %s" % (form.cleaned_data['track'], filename)

            destfilename = "%s/%s" % (fulldirname, filename)

            if isfile(destfilename):
                messages.add_message(request, messages.ERROR, 'File already exists: %s' % destfilename)
            else:
                move("/tmp/%s" % md5sum, destfilename)

            # If album artwork is not found on the filesystem, create it
            artwork_file = "%s/artwork.jpg" % (fulldirname)
            if not isfile(artwork_file):
                audio = MP3(destfilename)
                if 'APIC:' in audio.tags:
                    artwork = audio.tags['APIC:']
                    fh = open(artwork_file, "w")
                    fh.write(artwork.data)
                    fh.close()

            if not messages.get_messages(request):
                action = 'Upload'
                md5sum = None
                if a:
                    listen_url = reverse('show_album', args=[album_id])
                else:
                    listen_url = reverse('show_artist', args=[form.cleaned_data['artist']])
                messages.add_message(request, messages.INFO, 'Song successfully added.  <a href="' + listen_url + '">Listen to it here.</a>')
            else:
                action = 'Review'

        else:
            action = 'Review'


    return render_to_response('music/add_song.html',
                              {'section': SECTION, 'action': action, 'info': info, 'notes': notes, 'md5sum': md5sum, 'form': form },
                              context_instance=RequestContext(request))


class MusicListJson(BaseDatatableView):
    # define column names that will be used in sorting
    # order is important and should be same as order of columns
    # displayed by datatables. For non sortable columns use empty
    # value like ''
    order_columns = ['created', 'artist', 'title']

    def get_initial_queryset(self):
        # return queryset used as base for futher sorting/filtering
        # these are simply objects displayed in datatable
        return Song.objects.all()

    def filter_queryset(self, qs):
        # use request parameters to filter queryset

        # simple example:
        sSearch = self.request.GET.get('sSearch', None)
        if sSearch:
            qs = qs.filter(
                Q( title__icontains=sSearch ) |
                Q( artist__icontains=sSearch )
                )

        # more advanced example
        # filter_customer = self.request.GET.get('customer', None)

        # if filter_customer:
        #     customer_parts = filter_customer.split(' ')
        #     qs_params = None
        #     for part in customer_parts:
        #         q = Q(customer_firstname__istartswith=part)|Q(customer_lastname__istartswith=part)
        #         qs_params = qs_params | q if qs_params else q
        #         qs = qs.filter(qs_params)

        return qs

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here

        json_data = []
        for item in qs:
            json_data.append([
                item.created.strftime("%b %d, %Y"),
                item.artist,
                item.title,
                item.id
                # "%s %s" % (item.customer_firstname, item.customer_lastname),
                # item.get_state_display(),
                # item.modified.strftime("%Y-%m-%d %H:%M:%S")
            ])
        return json_data

@login_required
def search(request):

    import json

    # The search could match an album name or an artist or a song title
    albums = Album.objects.filter( title__icontains=request.GET['query'])
    artists = Song.objects.filter( artist__icontains=request.GET['query'] ).distinct('artist')
    songs = Song.objects.filter( title__icontains=request.GET['query']).order_by('title')

    results = []

    for album in albums:
        results.append( { 'label': "%s - %s" % (album.artist, album.title),
                          'id': album.id,
                          'type': 'album' } )

    for artist in artists:
        results.append( { 'label': "%s" % (artist.artist),
                          'type': 'artist' } )

    for song in songs:
        results.append( { 'label': "%s - %s" % (song.title, song.artist),
                          'id': song.album_id,
                          'type': 'album' } )

    json_text = json.dumps(results)

    return render_to_response('music/music_search.json',
                              {'section': SECTION, 'info': json_text},
                              context_instance=RequestContext(request),
                              mimetype="application/json")

class WishListView(ListView):

    model = WishList
    template_name = "music/wishlist.html"
    context_object_name = "info"

    def get_context_data(self, **kwargs):
        context = super(WishListView, self).get_context_data(**kwargs)

        info = []

        for myobject in kwargs['object_list']:
            info.append( dict(artist=myobject.artist, song=myobject.song, album=myobject.album, created=myobject.get_created(), unixtime=format(myobject.created, 'U'), wishlistid=myobject.id) )


        context['cols'] = ['artist', 'song', 'album', 'created', 'wishlistid']
        context['section'] = SECTION
        context['info'] = info
        return context


class WishListDetailView(UpdateView):
    template_name = 'music/wishlist_edit.html'
    form_class = WishListForm

    def get_context_data(self, **kwargs):
        context = super(WishListDetailView, self).get_context_data(**kwargs)
        context['section'] = SECTION
        context['pk'] = self.kwargs.get('pk')
        context['action'] = 'Edit'
        return context

    def get_object(self, queryset=None):
        obj = WishList.objects.get(user=self.request.user, id=self.kwargs.get('pk'))
        return obj

    def form_valid(self, form):

        self.object = form.save()
        context = self.get_context_data(form=form)
        context["message"] = "Wishlist updated"
        return self.render_to_response(context)


class WishListCreateView(CreateView):
    template_name = 'music/wishlist_edit.html'
    form_class = WishListForm

    def get_context_data(self, **kwargs):
        context = super(WishListCreateView, self).get_context_data(**kwargs)
        context['section'] = SECTION
        context['action'] = 'Add'
        return context

    def get_form_kwargs(self):
        # pass the request object to the form so that we have access to the session
        kwargs = super(WishListCreateView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()

        return HttpResponseRedirect(self.get_success_url())


    def get_success_url(self):
        return reverse('wishlist')
