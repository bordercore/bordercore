import hashlib
import os
import re
import time
from datetime import datetime

import boto3

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.forms.utils import ErrorList
from django.http import (HttpResponse, HttpResponseNotFound,
                         HttpResponseRedirect, JsonResponse)
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from django_datatables_view.base_datatable_view import BaseDatatableView
from lib.util import remove_non_ascii_characters
from music.forms import SongForm, WishListForm
from music.models import Album, Listen, Song, SongSource, WishList
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

SECTION = 'Music'
MUSIC_ROOT = "/home/media/music"


@login_required
def music_list(request):

    message = ''

    # Get a list of recently played songs
    recent_songs = Listen.objects.filter(user=request.user).select_related().distinct().order_by('-created')[:5]

    # Get a random album
    random_albums = None
    random_album_info = Album.objects.filter(user=request.user).order_by('?')
    if random_album_info:
        random_albums = random_album_info[0]

    return render(request, 'music/index.html',
                  {'section': SECTION,
                   'cols': ['Date', 'artist', 'title', 'id'],
                   'message': message,
                   'recent_songs': recent_songs,
                   'random_albums': random_albums,
                   'title': 'Music List',
                   'MEDIA_URL_MUSIC': settings.MEDIA_URL_MUSIC
                   })


@login_required
def album_artwork(request, song_id):

    if len(song_id) == 32:
        file_path = "/tmp/{}".format(song_id)
    else:
        song = Song.objects.get(user=request.user, id=song_id)

        if not song.album:
            return HttpResponseNotFound()

        tracknumber = str(song.track)
        if len(tracknumber) == 1:
            tracknumber = '0' + tracknumber

            file_path = "{}/{}/{}/{} - {}.mp3".format(MUSIC_ROOT, song.artist, song.album.title, tracknumber, song.title)

    audio = MP3(file_path)
    artwork = audio.tags.get('APIC:')

    if artwork:
        return HttpResponse(artwork.data, content_type=artwork.mime)
    else:
        return redirect("https://www.bordercore.com/static/img/image_not_found.jpg")


@login_required
def song_edit(request, song_id=None):

    action = 'Edit'
    file_info = None

    song = Song.objects.get(user=request.user, pk=song_id) if song_id else None

    tracknumber = str(song.track)
    if len(tracknumber) == 1:
        tracknumber = '0' + tracknumber

    if song.album:
        filename = "{}/{}/{}/{} - {}.mp3".format(MUSIC_ROOT, song.artist, song.album.title, tracknumber, song.title)
        try:
            id3_info = MP3(filename)
            file_info = {'id3_info': id3_info,
                         'filesize': os.stat(filename).st_size,
                         'length': time.strftime('%M:%S', time.gmtime(id3_info.info.length))}
        except IOError as e:
            messages.add_message(request, messages.ERROR, 'IOError: {}'.format(e))

    if request.method == 'POST':
        if request.POST['Go'] in ['Edit', 'Add']:
            form = SongForm(request.POST, instance=song)
            if form.is_valid():
                newform = form.save(commit=False)
                newform.user = request.user
                newform.save()
                form.save_m2m()
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
        form = SongForm()  # An unbound form

    return render(request, 'music/edit.html',
                  {'section': SECTION,
                   'action': action,
                   'form': form,
                   'file_info': file_info,
                   'song': song})


@method_decorator(login_required, name='dispatch')
class AlbumDetailView(DetailView):

    model = Album

    def get_context_data(self, **kwargs):
        context = super(AlbumDetailView, self).get_context_data(**kwargs)

        context['a'] = self.object
        s = Song.objects.filter(user=self.request.user, album=self.object).order_by('track')

        song_list = []

        for song in s:
            if self.object.compilation:
                display_title = song.title + ' - ' + song.artist
            else:
                display_title = song.title
            song_list.append(dict(id=song.id,
                                  track=song.track,
                                  raw_title=song.title.replace('/', 'FORWARDSLASH'),
                                  title=display_title,
                                  length_seconds=song.length,
                                  length=time.strftime('%M:%S', time.gmtime(song.length))))

        context['song_list'] = song_list
        context['title'] = 'Album Detail :: {}'.format(self.object.title)
        context['cols'] = ['id', 'track', 'raw_title', 'title', 'length', 'length_seconds']
        context['MEDIA_URL_MUSIC'] = settings.MEDIA_URL_MUSIC
        context['section'] = SECTION

        return context

    def get_queryset(self):
        return Album.objects.filter(user=self.request.user)


@login_required
def artist_detail(request, artist_name):

    # Get all albums by this artist
    a = Album.objects.filter(user=request.user, artist=artist_name).order_by('-original_release_year')

    # Get all songs by this artist that do not appear on an album
    s = Song.objects.filter(user=request.user, artist=artist_name).filter(album__isnull=True)

    # Get all songs by this artist that do appear on compilation album
    c = Album.objects.filter(Q(user=request.user) & Q(song__artist=artist_name) & ~Q(artist=artist_name)).distinct('song__album')

    song_list = []

    for song in s:
        song_list.append(dict(id=song.id,
                              year=song.year,
                              title=song.title,
                              length_seconds=song.length,
                              length=time.strftime('%M:%S', time.gmtime(song.length)),
                              artist=song.artist,
                              info=song.comment))

    return render(request, 'music/artist_detail.html',
                  {
                      'section': SECTION,
                      'artist_name': artist_name,
                      'album_list': a,
                      'song_list': song_list,
                      'compilation_album_list': c,
                      'cols': ['year', 'artist', 'title', 'length', 'length_seconds', 'info', 'id'],
                      'title': 'Artist Detail :: {}'.format(artist_name),
                      'MEDIA_URL_MUSIC': settings.MEDIA_URL_MUSIC
                  })


@login_required
def add_song(request):

    info = {}
    notes = []
    sha1sum = None
    form = None
    action = 'Upload'

    if 'upload' in request.POST:

        formdata = {}

        action = 'Review'
        blob = request.FILES['song'].read()
        sha1sum = hashlib.sha1(blob).hexdigest()
        filename = f"/tmp/{sha1sum}"

        try:
            f = open(filename, "wb")
            f.write(blob)
            f.close()
        except (IOError) as e:
            messages.add_message(request, messages.ERROR, f'IOError: {e}')

        info = MP3(filename, ID3=EasyID3)

        for field in ('artist', 'title', 'album'):
            formdata[field] = info[field][0] if info.get(field) else None
        if info.get('date'):
            formdata['year'] = info['date'][0]
        formdata['length'] = int(info.info.length)

        # I usually buy my music from Amazon, so set that as the default
        formdata['source'] = SongSource.objects.get(name='Amazon').id

        if info.get('album') and info.get('artist'):
            if info.get('album'):
                if Album.objects.filter(user=request.user, title=info['album'][0], artist=info['artist'][0]):
                    notes.append('You already have an album with this title')
                # Look for a fuzzy match
                fuzzy_matches = Album.objects.filter(Q(user=request.user) & Q(title__icontains=info['title'][0].lower()))
                if fuzzy_matches:
                    notes.append(f'Found a fuzzy match on the album title: "{fuzzy_matches[0].title}" by {fuzzy_matches[0].artist}')

            if Song.objects.filter(user=request.user, title=info['title'][0], artist=info['artist'][0]):
                notes.append('You already have a song with this title by this artist')

        if info.get('tracknumber'):
            track_info = info['tracknumber'][0].split('/')
            track_number = track_info[0]
            formdata['track'] = track_number

        form = SongForm(initial=formdata)

        # This should initialize form._errors, used below
        form.full_clean()

        if formdata.get('year') and not re.search(r'^\d+$', formdata['year']):
            form._errors["year"] = ErrorList([u"Wrong format"])

    elif 'add' in request.POST:

        sha1sum = request.POST['sha1sum']

        if request.POST['year']:
            try:
                song = Song.objects.get(user=request.user, artist=request.POST['artist'], title=request.POST['title'], year=request.POST['year'])
            except ObjectDoesNotExist:
                song = None
        else:
            song = None

        form = SongForm(request.POST, instance=song)  # A form bound to the POST data

        info = MP3(f"/tmp/{sha1sum}", ID3=EasyID3)

        if form.is_valid():

            album_id = None

            album_title = request.POST.get("album", "").strip()

            # If an album was specified, check if we have the album
            if album_title:
                album_artist = form.cleaned_data['artist']
                if request.POST.get('compilation'):
                    album_artist = "Various Artists"
                try:
                    a = Album.objects.get(user=request.user, title=album_title, artist=album_artist)
                except ObjectDoesNotExist:
                    a = None
                if a:
                    if a.year != form.cleaned_data['year']:
                        messages.add_message(request, messages.ERROR, 'The same album exists but with a different year')
                else:
                    # This is a new album
                    a = Album(user=request.user,
                              title=album_title,
                              artist=album_artist,
                              year=form.cleaned_data['year'],
                              original_release_year=request.POST['original_release_year'] if request.POST['original_release_year'] else form.cleaned_data['year'],
                              compilation=True if 'compilation' in request.POST else False)
            else:
                # No album was specified
                a = None

            if not messages.get_messages(request):
                if a:
                    a.save()
                form.cleaned_data['length'] = int(info.info.length)
                new_song = form.save(commit=False)
                if a:
                    new_song.album = a
                new_song.user = request.user

                new_song.save()

                # Take care of the tags.  Create any that are new.
                for tag in form.cleaned_data['tags']:
                    new_song.tags.add(tag)

            if a:
                album_id = a.id

            s3_client = boto3.client("s3")
            key = f"songs/{new_song.uuid}"

            # Note: S3 Metadata cannot contain non ASCII characters
            s3_client.upload_file(
                f"/tmp/{sha1sum}",
                settings.AWS_BUCKET_NAME_MUSIC,
                key,
                ExtraArgs={
                    "Metadata": {
                        "artist": remove_non_ascii_characters(form.cleaned_data["artist"], default="Artist"),
                        "title": remove_non_ascii_characters(form.cleaned_data["title"], default="Title")
                    }
                }
            )

            audio = MP3(f"/tmp/{sha1sum}")

            if audio:
                artwork = audio.tags.getall("APIC")
                if artwork:

                    artwork_file = f"/tmp/{sha1sum}-artwork.jpg"

                    fh = open(artwork_file, "wb")
                    fh.write(artwork[0].data)
                    fh.close()

                    key = f"artwork/{album_id}"
                    s3_client.upload_file(
                        artwork_file,
                        settings.AWS_BUCKET_NAME_MUSIC,
                        key)

                    os.remove(artwork_file)

            os.remove(f"/tmp/{sha1sum}")

            if not messages.get_messages(request):
                action = 'Upload'
                sha1sum = None
                if a:
                    listen_url = reverse('album_detail', args=[album_id])
                else:
                    listen_url = reverse('artist_detail', args=[form.cleaned_data['artist']])
                messages.add_message(request, messages.INFO, 'Song successfully added.  <a href="' + listen_url + '">Listen to it here.</a>')
            else:
                action = 'Review'

        else:
            action = 'Review'

    return render(request, 'music/add_song.html',
                  {'section': SECTION,
                   'action': action,
                   'info': info,
                   'notes': notes,
                   'sha1sum': sha1sum,
                   'form': form,
                   'title': 'Add Song'})


@method_decorator(login_required, name='dispatch')
class MusicListJson(BaseDatatableView):
    # define column names that will be used in sorting
    # order is important and should be same as order of columns
    # displayed by datatables. For non sortable columns use empty
    # value like ''
    order_columns = ['created', 'artist', 'title']

    def get_initial_queryset(self):
        # return queryset used as base for futher sorting/filtering
        # these are simply objects displayed in datatable
        return Song.objects.filter(user=self.request.user)

    def filter_queryset(self, qs):
        # use request parameters to filter queryset

        # simple example:
        sSearch = self.request.GET.get('sSearch', None)
        if sSearch:
            qs = qs.filter(
                Q(title__icontains=sSearch) |
                Q(artist__icontains=sSearch)
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
            ])
        return json_data


@login_required
def search(request):

    # The search could match an album name or an artist or a song title
    albums = Album.objects.filter(user=request.user, title__icontains=request.GET['query'])
    artists = Song.objects.filter(user=request.user, artist__icontains=request.GET['query']).distinct('artist').order_by('artist')
    songs = Song.objects.filter(user=request.user, title__icontains=request.GET['query']).order_by('title')

    results = []

    for album in albums:
        results.append({'name': '{} - {}'.format(album.artist, album.title),
                        'value': '{} - {}'.format(album.artist, album.title),
                        'id': album.id,
                        'type': 'album'})

    for artist in artists:
        results.append({'name': '{}'.format(artist.artist),
                        'value': '{}'.format(artist.artist),
                        'type': 'artist'})

    for song in songs:
        # If we don't have the album for the song (eg it's a "loose" song), return an 'artist' result,
        #  otherwise return the 'album' result
        if song.album_id:
            results.append({'name': '{} - {}'.format(song.title, song.artist),
                            'value': '{} - {}'.format(song.title, song.artist),
                            'id': song.album_id,
                            'type': 'album'})
        else:
            results.append({'name': '{} - {}'.format(song.title, song.artist),
                            'value': '{}'.format(song.artist),
                            'type': 'artist'})

    return JsonResponse(results, safe=False)


def get_song_location(song):

    song_title = song.title.replace("/", "FORWARDSLASH")

    # If the song is associated with an album, look for it in the album's directory
    if song.album:
        if song.album.compilation:
            artist_name = 'Various'
        else:
            artist_name = song.artist
        tracknumber = str(song.track)
        if len(tracknumber) == 1:
            tracknumber = '0' + tracknumber
        file_info = {'url': '/music/{}/{}/{} - {}.mp3'.format(artist_name, song.album.title, tracknumber, song_title)}
    else:
        file_info = {'url': '/music/{}/{}.mp3'.format(song.artist, song_title)}

        if not os.path.isfile('/home/media/{}'.format(file_info['url'])):
            # Check this type of file path: /home/media/mp3/Primitives - Crash.mp3
            file_info = {'url': '/mp3/{} - {}.mp3'.format(song.artist, song_title)}

            if not os.path.isfile('/home/media/{}'.format(file_info['url'])):
                # Check this type of file path: /home/media/mp3/m/Motley Crue - She's Got Looks That Kill.mp3
                file_info = {'url': '/mp3/{}/{} - {}.mp3'.format(song.artist[0].lower(), song.artist, song_title)}

    return file_info


@login_required
def get_song_info(request, id):

    song = Song.objects.get(user=request.user, pk=id)

    # Indicate that this song has been listened to, but only if we're in production
    if not settings.DEBUG:
        if song.times_played:
            song.times_played = song.times_played + 1
        else:
            song.times_played = 1

        song.last_time_played = datetime.now()
        song.save()

        Listen(song=song, user=request.user).save()

    file_location = f"{settings.MEDIA_URL_MUSIC}songs/{song.uuid}"

    results = {'title': song.title,
               'url': file_location}

    return JsonResponse(results)


@method_decorator(login_required, name='dispatch')
class WishListView(ListView):

    model = WishList
    template_name = "music/wishlist.html"
    context_object_name = "info"

    def get_queryset(self):
        return WishList.objects.filter(user=self.request.user).order_by('-created')

    def get_context_data(self, **kwargs):
        context = super(WishListView, self).get_context_data(**kwargs)

        info = []

        for myobject in context['object_list']:
            info.append(dict(
                artist=myobject.artist,
                song=myobject.song,
                album=myobject.album,
                created=myobject.get_created(),
                unixtime=format(myobject.created, 'U'),
                wishlistid=myobject.id))

        context['cols'] = ['artist', 'song', 'album', 'created', 'wishlistid']
        context['section'] = SECTION
        context['info'] = info
        context['title'] = 'Wishlist'
        return context


@method_decorator(login_required, name='dispatch')
class WishListDetailView(UpdateView):
    template_name = 'music/wishlist_edit.html'
    form_class = WishListForm

    def get_context_data(self, **kwargs):
        context = super(WishListDetailView, self).get_context_data(**kwargs)
        context['section'] = SECTION
        context['pk'] = self.kwargs.get('pk')
        context['action'] = 'Edit'
        context['title'] = 'Wishlist Detail :: {} - {}'.format(self.object.artist, self.object.song)
        return context

    def get_object(self, queryset=None):
        obj = WishList.objects.get(user=self.request.user, id=self.kwargs.get('pk'))
        return obj

    def form_valid(self, form):
        self.object = form.save()
        messages.add_message(self.request, messages.INFO, 'Wishlist edited')
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('wishlist')


@method_decorator(login_required, name='dispatch')
class WishListCreateView(CreateView):
    template_name = 'music/wishlist_edit.html'
    form_class = WishListForm

    def get_context_data(self, **kwargs):
        context = super(WishListCreateView, self).get_context_data(**kwargs)
        context['section'] = SECTION
        context['action'] = 'Add'
        context['title'] = 'Wishlist Edit'
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


@login_required
def wishlist_delete(request, wishlist_id=None):
    wishlist = WishList.objects.get(user=request.user, id=wishlist_id)
    wishlist.delete()

    return JsonResponse("OK", safe=False)
