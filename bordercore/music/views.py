import os
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

import boto3
from elasticsearch import Elasticsearch
from mutagen.mp3 import MP3

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from lib.time_utils import convert_seconds
from lib.util import remove_non_ascii_characters
from music.forms import SongForm
from music.models import Album, Listen, Song

MUSIC_ROOT = "/home/media/music"


@login_required
def music_list(request):

    message = ""

    # Get a list of recently played songs
    recent_songs = Listen.objects.filter(user=request.user).select_related("song").distinct().order_by("-created")[:10]

    # Get a random album
    random_albums = None
    random_album_info = Album.objects.filter(user=request.user).order_by("?")
    if random_album_info:
        random_albums = random_album_info.first()

    return render(request, "music/index.html",
                  {
                      "cols": ["Date", "artist", "title", "id"],
                      "message": message,
                      "recent_songs": recent_songs,
                      "random_albums": random_albums,
                      "title": "Music List",
                      "MEDIA_URL_MUSIC": settings.MEDIA_URL_MUSIC,
                  })


@method_decorator(login_required, name="dispatch")
class ArtistDetailView(TemplateView):

    template_name = "music/artist_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        artist_name = self.kwargs.get("artist")

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
                                  length=convert_seconds(song.length),
                                  artist=song.artist,
                                  note=re.sub("[\n\r\"]", "", song.note or "")))

        return {
            **context,
            "artist_name": artist_name,
            "album_list": albums,
            "song_list": song_list,
            "compilation_album_list": compilation_songs,
            "MEDIA_URL_MUSIC": settings.MEDIA_URL_MUSIC
        }


@method_decorator(login_required, name="dispatch")
class AlbumDetailView(DetailView):

    model = Album
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["a"] = self.object
        s = Song.objects.filter(user=self.request.user, album=self.object).order_by("track")

        song_list = []

        for song in s:
            if self.object.compilation:
                display_title = song.title + " - " + song.artist
            else:
                display_title = song.title
            song_list.append(dict(uuid=song.uuid,
                                  track=song.track,
                                  raw_title=song.title.replace("/", "FORWARDSLASH"),
                                  title=display_title,
                                  note=song.note,
                                  length_seconds=song.length,
                                  length=convert_seconds(song.length)))

        return {
            **context,
            "song_list": song_list,
            "MEDIA_URL_MUSIC": settings.MEDIA_URL_MUSIC
        }

    def get_queryset(self):
        return Album.objects.filter(user=self.request.user)


@method_decorator(login_required, name="dispatch")
class SongUpdateView(UpdateView):

    model = Song
    template_name = "music/create_song.html"
    form_class = SongForm
    success_url = reverse_lazy("music:list")
    slug_field = "uuid"
    slug_url_kwarg = "song_uuid"

    # Override this method so that we can pass the request object to the form
    #  so that we have access to it in SongForm.__init__()
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Update"
        context["song_length_pretty"] = convert_seconds(self.object.length)
        context["tags"] = [{"text": x.name, "value": x.name, "is_meta": x.is_meta} for x in self.object.tags.all()]
        return context

    def form_valid(self, form):
        song = form.instance

        # Delete all existing tags
        song.tags.clear()

        # Then add the tags specified in the form
        for tag in form.cleaned_data["tags"]:
            song.tags.add(tag)

        self.object = form.save()

        messages.add_message(
            self.request, messages.INFO,
            "Song updated"
        )

        return HttpResponseRedirect(self.get_success_url())


@method_decorator(login_required, name="dispatch")
class SongCreateView(CreateView):
    model = Song
    template_name = "music/create_song.html"
    form_class = SongForm
    success_url = reverse_lazy("music:create")

    # Override this method so that we can pass the request object to the form
    #  so that we have access to it in SongForm.__init__()
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


@method_decorator(login_required, name="dispatch")
class MusicDeleteView(DeleteView):
    model = Song
    success_url = reverse_lazy("music:list")

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.add_message(self.request, messages.INFO, "Song successfully deleted")
        return response

    def get_object(self, queryset=None):
        song = Song.objects.get(user=self.request.user, uuid=self.kwargs.get("uuid"))
        return song


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

            key = f"artwork/{song.album.uuid}"
            s3_client.upload_file(
                artwork_file,
                settings.AWS_BUCKET_NAME_MUSIC,
                key,
                ExtraArgs={"ContentType": "image/jpeg"}
            )

            os.remove(artwork_file)


@login_required
def search_artists(request):

    es = Elasticsearch(
        [settings.ELASTICSEARCH_ENDPOINT],
        verify_certs=False
    )

    search_terms = re.split(r"\s+", unquote(request.GET["term"].lower()))

    search_object = {
        "query": {
            "bool": {
                "must": [
                    {
                        "term": {
                            "doctype": "song"
                        }
                    },
                    {
                        "term": {
                            "user_id": request.user.id
                        }
                    }
                ]
            }
        },
        "aggs": {
            "unique_artists": {
                "terms": {
                    "field": "artist.keyword",
                    "size": 100
                }
            }
        },
        "from": 0, "size": 0,
        "_source": ["artist"]
    }

    # Separate query into terms based on whitespace and
    #  and treat it like an "AND" boolean search
    for one_term in search_terms:
        search_object["query"]["bool"]["must"].append(
            {
                "bool": {
                    "should": [
                        {
                            "wildcard": {
                                "artist": {
                                    "value": f"*{one_term}*",
                                }
                            }
                        }
                    ]
                }
            }
        )

    results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)
    matches = []

    for match in results["aggregations"]["unique_artists"]["buckets"]:

        matches.append(
            {
                "artist": match["key"]
            }
        )

    return JsonResponse(matches, safe=False)


@method_decorator(login_required, name="dispatch")
class RecentSongsListView(ListView):

    def get_queryset(self):
        search_term = self.request.GET.get("tag", None)

        queryset = Song.objects.filter(user=self.request.user)

        if search_term:
            queryset = queryset.filter(
                Q(title__icontains=search_term)
                | Q(artist__icontains=search_term)
            )

        return queryset.order_by("-created", "artist", "title")[:20]

    def get(self, request, *args, **kwargs):

        queryset = self.get_queryset()

        song_list = []

        for match in queryset:
            song_list.append(
                {
                    "uuid": match.uuid,
                    "title": match.title,
                    "artist": match.artist,
                    "year": match.year,
                    "length": convert_seconds(match.length),
                    "artist_url": reverse("music:artist_detail", kwargs={"artist": match.artist})
                }
            )

        response = {
            "status": "OK",
            "song_list": song_list
        }

        return JsonResponse(response)


def get_song_location(song):

    song_title = song.title.replace("/", "FORWARDSLASH")

    # If the song is associated with an album, look for it in the album's directory
    if song.album:
        if song.album.compilation:
            artist_name = "Various"
        else:
            artist_name = song.artist
        tracknumber = str(song.track)
        if len(tracknumber) == 1:
            tracknumber = "0" + tracknumber
        file_info = {"url": "/music/{}/{}/{} - {}.mp3".format(artist_name, song.album.title, tracknumber, song_title)}
    else:
        file_info = {"url": "/music/{}/{}.mp3".format(song.artist, song_title)}

        if not Path("/home/media/{}".format(file_info["url"])).is_file():
            # Check this type of file path: /home/media/mp3/Primitives - Crash.mp3
            file_info = {"url": "/mp3/{} - {}.mp3".format(song.artist, song_title)}

            if not Path("/home/media/{}".format(file_info["url"])).is_file():
                # Check this type of file path: /home/media/mp3/m/Motley Crue - She's Got Looks That Kill.mp3
                file_info = {"url": "/mp3/{}/{} - {}.mp3".format(song.artist[0].lower(), song.artist, song_title)}

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

    results = {"title": song.title,
               "url": file_location}

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

        song_list = []

        for match in context["object_list"]:
            song_list.append(
                {
                    "uuid": match.uuid,
                    "title": match.title,
                    "artist": match.artist,
                    "year": match.year,
                    "length": convert_seconds(match.length)
                }
            )

        return {
            **context,
            "tag_name": self.request.GET["tag"],
            "song_list": song_list
        }
