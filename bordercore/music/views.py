import os
from datetime import datetime
from pathlib import Path

import boto3
from django_datatables_view.base_datatable_view import BaseDatatableView
from mutagen.mp3 import MP3

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from lib.time_utils import convert_seconds
from lib.util import remove_non_ascii_characters
from music.forms import SongForm
from music.models import Album, Listen, Song

MUSIC_ROOT = "/home/media/music"


@login_required
def music_list(request):

    message = ''

    # Get a list of recently played songs
    recent_songs = Listen.objects.filter(user=request.user).select_related("song").distinct().order_by('-created')[:10]

    # Get a random album
    random_albums = None
    random_album_info = Album.objects.filter(user=request.user).order_by('?')
    if random_album_info:
        random_albums = random_album_info.first()

    return render(request, 'music/index.html',
                  {'cols': ['Date', 'artist', 'title', 'id'],
                   'message': message,
                   'recent_songs': recent_songs,
                   'random_albums': random_albums,
                   'title': 'Music List',
                   'MEDIA_URL_MUSIC': settings.MEDIA_URL_MUSIC
                   })


@login_required
def song_update(request, song_uuid=None):

    action = 'Update'
    file_info = None

    song = Song.objects.get(user=request.user, uuid=song_uuid) if song_uuid else None

    tracknumber = str(song.track)
    if len(tracknumber) == 1:
        tracknumber = '0' + tracknumber

    if song.album:
        filename = "{}/{}/{}/{} - {}.mp3".format(MUSIC_ROOT, song.artist, song.album.title, tracknumber, song.title)
        try:
            id3_info = MP3(filename)
            file_info = {'id3_info': id3_info,
                         'filesize': os.stat(filename).st_size,
                         'length': convert_seconds(id3_info.info.length)}
        except IOError as e:
            messages.add_message(request, messages.ERROR, 'IOError: {}'.format(e))

    if request.method == 'POST':
        if request.POST['Go'] in ['Update', 'Create']:
            form = SongForm(request.POST, instance=song, request=request)
            if form.is_valid():
                newform = form.save(commit=False)
                newform.user = request.user
                newform.save()
                form.save_m2m()
                messages.add_message(request, messages.INFO, 'Song updated')
                return music_list(request)
        elif request.POST['Go'] == 'Delete':
            song.delete()
            messages.add_message(request, messages.INFO, 'Song deleted')
            return music_list(request)

    elif song_uuid:
        action = 'Update'
        form = SongForm(instance=song, request=request)

    else:
        action = 'Create'
        form = SongForm(request=request)

    return render(request, 'music/update.html',
                  {'action': action,
                   'form': form,
                   'file_info': file_info,
                   'length': convert_seconds(song.length),
                   'tags': [{"text": x.name, "value": x.name, "is_meta": x.is_meta} for x in song.tags.all()],
                   'song': song})


@method_decorator(login_required, name='dispatch')
class ArtistDetailView(TemplateView):

    template_name = "music/artist_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        artist_name = self.kwargs.get("artist")

        print(f"GOT HERE: {artist_name}")

        # Get all albums by this artist
        albums = Album.objects.filter(user=self.request.user, artist=artist_name).order_by("-original_release_year")

        # Get all songs by this artist that do not appear on an album
        songs = Song.objects.filter(user=self.request.user, artist=artist_name).filter(album__isnull=True)

        # Get all songs by this artist that do appear on compilation album
        compilation_songs = Album.objects.filter(
            Q(user=self.request.user)
            & Q(song__artist=artist_name)
            & ~Q(artist=artist_name)
        ).distinct("song__album")

        song_list = []

        for song in songs:
            song_list.append(dict(uuid=song.uuid,
                                  year=song.year,
                                  title=song.title,
                                  length_seconds=song.length,
                                  length=convert_seconds(song.length),
                                  artist=song.artist,
                                  info=song.comment))

        context = {
            "artist_name": artist_name,
            "album_list": albums,
            "song_list": song_list,
            "compilation_album_list": compilation_songs,
            "cols": ["year", "artist", "title", "length", "length_seconds", "info", "uuid"],
            "title": f"Artist Detail :: {artist_name}",
            "MEDIA_URL_MUSIC": settings.MEDIA_URL_MUSIC
        }

        return context


@method_decorator(login_required, name='dispatch')
class AlbumDetailView(DetailView):

    model = Album
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['a'] = self.object
        s = Song.objects.filter(user=self.request.user, album=self.object).order_by('track')

        song_list = []

        for song in s:
            if self.object.compilation:
                display_title = song.title + ' - ' + song.artist
            else:
                display_title = song.title
            song_list.append(dict(uuid=song.uuid,
                                  track=song.track,
                                  raw_title=song.title.replace('/', 'FORWARDSLASH'),
                                  title=display_title,
                                  length_seconds=song.length,
                                  length=convert_seconds(song.length)))

        context['song_list'] = song_list
        context['title'] = 'Album Detail :: {}'.format(self.object.title)
        context['cols'] = ['uuid', 'track', 'raw_title', 'title', 'length', 'length_seconds']
        context['MEDIA_URL_MUSIC'] = settings.MEDIA_URL_MUSIC

        return context

    def get_queryset(self):
        return Album.objects.filter(user=self.request.user)


@method_decorator(login_required, name='dispatch')
class SongCreateView(CreateView):
    model = Song
    template_name = "music/create_song.html"
    form_class = SongForm
    success_url = reverse_lazy("music:create_song")

    # Override this method so that we can pass the request object to the form
    #  so that we have access to it in TodoForm.__init__()
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Create"
        return context

    def form_valid(self, form):

        album_info = Song.get_album_info(self.request.user, form.cleaned_data)

        song = form.save(commit=False)
        song.user = self.request.user
        song.save()

        # Take care of the tags.  Create any that are new.
        for tag in form.cleaned_data["tags"]:
            song.tags.add(tag)

        # If an album name was specified, associate it with the song
        if album_info:
            song.album = album_info

        song.save()

        # Upload the song and its artwork to S3
        handle_s3(song, form.cleaned_data["sha1sum"])

        # Remove the uploaded song from /tmp
        os.remove(f"/tmp/{self.request.user.userprofile.uuid}-{form.cleaned_data['sha1sum']}.mp3")

        # Save the song source in the session
        self.request.session["song_source"] = form.cleaned_data["source"].name

        listen_url = Song.get_song_url(song)
        messages.add_message(
            self.request, messages.INFO,
            f"Song successfully created.  <a href='{listen_url}'>Listen to it here.</a>"
        )

        return super().form_valid(form)


def handle_s3(song, sha1sum):

    s3_client = boto3.client("s3")
    key = f"songs/{song.uuid}"

    # Note: S3 Metadata cannot contain non ASCII characters
    s3_client.upload_file(
        f"/tmp/{song.user.userprofile.uuid}-{sha1sum}.mp3",
        settings.AWS_BUCKET_NAME_MUSIC,
        key,
        ExtraArgs={
            "Metadata": {
                "artist": remove_non_ascii_characters(song.artist, default="Artist"),
                "title": remove_non_ascii_characters(song.title, default="Title")
            }
        }
    )

    if not song.album:
        return

    audio = MP3(f"/tmp/{song.user.userprofile.uuid}-{sha1sum}.mp3")

    if audio:
        artwork = audio.tags.getall("APIC")
        if artwork:

            artwork_file = f"/tmp/{sha1sum}-artwork.jpg"

            fh = open(artwork_file, "wb")
            fh.write(artwork[0].data)
            fh.close()

            key = f"artwork/{song.album.id}"
            s3_client.upload_file(
                artwork_file,
                settings.AWS_BUCKET_NAME_MUSIC,
                key
            )

            os.remove(artwork_file)


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
                Q(title__icontains=sSearch)
                | Q(artist__icontains=sSearch)
            )

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

        if not Path('/home/media/{}'.format(file_info['url'])).is_file():
            # Check this type of file path: /home/media/mp3/Primitives - Crash.mp3
            file_info = {'url': '/mp3/{} - {}.mp3'.format(song.artist, song_title)}

            if not Path('/home/media/{}'.format(file_info['url'])).is_file():
                # Check this type of file path: /home/media/mp3/m/Motley Crue - She's Got Looks That Kill.mp3
                file_info = {'url': '/mp3/{}/{} - {}.mp3'.format(song.artist[0].lower(), song.artist, song_title)}

    return file_info


@login_required
def get_song_info(request, uuid):

    song = Song.objects.get(user=request.user, uuid=uuid)

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


@login_required
def get_song_id3_info(request):

    song = request.FILES["song"].read()
    id3_info = Song.get_id3_info(request, messages, song)
    return JsonResponse({**id3_info})


@method_decorator(login_required, name="dispatch")
class SearchTagListView(ListView):

    template_name = "music/tag_search.html"

    def get_queryset(self):
        tag_name = self.request.GET["tag"]

        return Song.objects.filter(user=self.request.user, tags__name=tag_name)

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        results = []

        for match in context["object_list"]:
            results.append(
                {
                    "title": match.title,
                    "artist": match.artist,
                    "year": match.year,
                    "length": convert_seconds(match.length),
                    "id": match.id,
                }
            )

        return {
            "cols": ["title", "artist", "year", "length", "id"],
            "tag_name": self.request.GET["tag"],
            "results": results,
        }
