import os
import time

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseNotFound
from django_datatables_view.base_datatable_view import BaseDatatableView
from mutagen.mp3 import MP3

from music.models import Album, Listen, Song
from music.forms import SongForm

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

    if not song.album:
        return HttpResponseNotFound()

    tracknumber = str(song.track)
    if len(tracknumber) == 1:
        tracknumber = '0' + tracknumber

    file_path = "%s/%s/%s/%s - %s.mp3" % (MUSIC_ROOT, song.artist, song.album.title, tracknumber, song.title)

    try:
        fsock = open(file_path, "r")
        response = HttpResponse( fsock, mimetype='audio/mpeg' )
    except IOError:
        response = HttpResponseNotFound()

    return response


@login_required
def album_artwork(request, song_id):

    song = Song.objects.get(id=song_id)

    if not song.album:
        return HttpResponseNotFound()

    tracknumber = str(song.track)
    if len(tracknumber) == 1:
        tracknumber = '0' + tracknumber

    file_path = "%s/%s/%s/%s - %s.mp3" % (MUSIC_ROOT, song.artist, song.album.title, tracknumber, song.title)

    audio = MP3(file_path)
    artwork = audio.tags['APIC:']

    try:
        response = HttpResponse( artwork.data, mimetype=artwork.mime )
    except IOError:
        response = HttpResponseNotFound()

    return response


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
        id3_info = MP3(filename)
        file_info = { 'id3_info': id3_info,
                      'filesize': os.stat(filename).st_size,
                      'length': time.strftime('%M:%S', time.gmtime( id3_info.info.length )) }

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

    album_list = Album.objects.filter(artist=artist_name).order_by('-year')

    return render_to_response('music/show_artist.html',
                              {'section': SECTION, 'album_list': album_list },
                              context_instance=RequestContext(request))


@login_required
def add_song(request):
    return render_to_response('music/add_song.html',
                              {'section': SECTION },
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
    artists = Album.objects.filter( artist__icontains=request.GET['query'] ).distinct('artist')
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
