import io
import json
import os
import re
import uuid
from datetime import timedelta

import boto3
import humanize
from mutagen.mp3 import MP3

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q
from django.forms.models import model_to_dict
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import (CreateView, DeleteView, ModelFormMixin,
                                       UpdateView)
from django.views.generic.list import ListView

from lib.mixins import FormRequestMixin
from lib.time_utils import convert_seconds
from lib.util import remove_non_ascii_characters
from music.services import search as search_service

from .forms import AlbumForm, PlaylistForm, SongForm
from .models import Album, Artist, Playlist, PlaylistItem, Song
from .services import get_playlist_counts, get_playlist_songs
from .services import get_recent_albums as get_recent_albums_service


@login_required
def music_list(request):

    recent_songs = Song.objects.filter(
        user=request.user
    ).select_related(
        "artist"
    ).order_by(
        F("last_time_played").desc(nulls_last=True)
    )[:10]

    # Get a random album to feature
    random_album = Album.objects.filter(user=request.user).select_related("artist").order_by("?").first()

    # Get all playlists and their song counts
    playlists = get_playlist_counts(request.user)

    page_number = request.GET.get("page_number", None)
    # Get a list of recently added albums
    recent_albums, paginator_info = get_recent_albums_service(request.user, page_number)

    # Verify that the user has at least one song in their collection
    collection_is_not_empty = Song.objects.filter(user=request.user).exists()

    return render(request, "music/index.html",
                  {
                      "cols": ["Date", "artist", "title", "id"],
                      "recent_songs": recent_songs,
                      "recent_albums": recent_albums,
                      "paginator_info": json.dumps(paginator_info),
                      "random_album": random_album,
                      "playlists": playlists,
                      "title": "Music List",
                      "collection_is_not_empty": collection_is_not_empty
                  })


@method_decorator(login_required, name="dispatch")
class ArtistDetailView(TemplateView):

    template_name = "music/artist_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        artist_uuid = self.kwargs.get("artist_uuid")

        artist = Artist.objects.get(uuid=artist_uuid)

        # Get all albums by this artist
        albums = Album.objects.filter(
            user=self.request.user,
            artist=artist
        ).order_by(
            "-original_release_year"
        )

        # Get all songs by this artist that do not appear on an album
        songs = Song.objects.filter(
            user=self.request.user,
            artist=artist
        ).filter(
            album__isnull=True
        ).order_by(
            F("year").desc(nulls_last=True),
            "title"
        )

        # Get all songs by this artist that do appear on compilation album
        compilation_songs = Album.objects.filter(
            Q(user=self.request.user)
            & Q(song__artist=artist)
            & ~Q(artist=artist)
        ).distinct("song__album")

        song_list = []

        for song in songs:
            song_list.append(dict(uuid=song.uuid,
                                  year_effective=song.original_year or song.year,
                                  title=song.title,
                                  length=convert_seconds(song.length),
                                  artist=song.artist,
                                  note=re.sub("[\n\r\"]", "", song.note or "")))

        return {
            **context,
            "artist_image": True,
            "artist": artist,
            "album_list": albums,
            "song_list": song_list,
            "compilation_album_list": compilation_songs,
        }


@method_decorator(login_required, name="dispatch")
class AlbumDetailView(FormRequestMixin, ModelFormMixin, DetailView):

    model = Album
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    form_class = AlbumForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        s = Song.objects.filter(user=self.request.user, album=self.object).order_by("track")

        playtime = self.object.playtime

        song_list = []

        for song in s:
            if self.object.compilation:
                display_title = song.title + " - " + song.artist.name
            else:
                display_title = song.title
            song_list.append(dict(uuid=song.uuid,
                                  track=song.track,
                                  raw_title=song.title.replace("/", "FORWARDSLASH"),
                                  title=display_title,
                                  note=song.note or "",
                                  length_seconds=song.length,
                                  length=convert_seconds(song.length)))

        return {
            **context,
            "song_list": song_list,
            "tags": [
                {
                    "text": x.name, "is_meta": x.is_meta
                } for x in self.object.tags.all()
            ],
            "playtime": playtime
        }

    def get_queryset(self):
        return Album.objects.filter(user=self.request.user)


@method_decorator(login_required, name="dispatch")
class AlbumUpdateView(FormRequestMixin, UpdateView):

    model = Album
    form_class = AlbumForm
    slug_field = "uuid"
    slug_url_kwarg = "album_uuid"
    template_name = "music/album_detail.html"

    def form_valid(self, form):

        if "cover_image" in self.request.FILES:
            self.handle_cover_image(form)

        song = form.instance

        # Delete all existing tags
        song.tags.clear()

        # Then add the tags specified in the form
        for tag in form.cleaned_data["tags"]:
            song.tags.add(tag)

        self.object = form.save()

        messages.add_message(
            self.request,
            messages.INFO,
            "Album updated"
        )

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):

        url = reverse(
            "music:album_detail",
            kwargs={
                "uuid": self.object.uuid
            }
        )

        # If we've uploaded a cover image, add a random UUID to the
        #  url to force the browser to evict the old image from cache
        #  so the new one is immediately visible.
        if "cover_image" in self.get_form_kwargs()["files"]:
            url = url + f"?cache_buster={uuid.uuid4()}"

        return url

    def handle_cover_image(self, form):
        """
        Upload the album's cover image to S3
        """

        s3_client = boto3.client("s3")

        key = f"album_artwork/{self.object.uuid}"
        fo = io.BytesIO(self.request.FILES["cover_image"].read())
        s3_client.upload_fileobj(
            fo,
            settings.AWS_BUCKET_NAME_MUSIC,
            key,
            ExtraArgs={"ContentType": "image/jpeg"}
        )


@method_decorator(login_required, name="dispatch")
class SongUpdateView(FormRequestMixin, UpdateView):

    model = Song
    template_name = "music/create_song.html"
    form_class = SongForm
    success_url = reverse_lazy("music:list")
    slug_field = "uuid"
    slug_url_kwarg = "song_uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Update"
        context["song_length_pretty"] = convert_seconds(self.object.length)
        context["tags"] = [{"text": x.name, "is_meta": x.is_meta} for x in self.object.tags.all()]
        context["tag_counts"] = Song.get_song_tags(self.request.user)
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

        if "return_url" in self.request.POST and self.request.POST["return_url"] != "":
            success_url = self.request.POST["return_url"]
        else:
            success_url = self.success_url

        return HttpResponseRedirect(success_url)


@method_decorator(login_required, name="dispatch")
class SongCreateView(FormRequestMixin, CreateView):
    model = Song
    template_name = "music/create_song.html"
    form_class = SongForm
    success_url = reverse_lazy("music:create")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Create"
        context["tag_counts"] = Song.get_song_tags(self.request.user)
        return context

    def form_valid(self, form):

        album_info = Song.get_album_info(self.request.user, form.cleaned_data)

        song = form.save(commit=False)
        song.user = self.request.user
        song.save()

        # Save the tags
        form.save_m2m()

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
                "artist": remove_non_ascii_characters(song.artist.name, default="Artist"),
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

            key = f"album_artwork/{song.album.uuid}"
            s3_client.upload_file(
                artwork_file,
                settings.AWS_BUCKET_NAME_MUSIC,
                key,
                ExtraArgs={"ContentType": "image/jpeg"}
            )

            os.remove(artwork_file)


@login_required
def search_artists(request):

    artist = request.GET["term"].lower()

    matches = search_service(request.user, artist)

    return JsonResponse(matches, safe=False)


@method_decorator(login_required, name="dispatch")
class RecentSongsListView(ListView):

    def get_queryset(self):
        search_term = self.request.GET.get("tag", None)

        queryset = Song.objects.filter(user=self.request.user) \
                               .filter(album__isnull=True) \
                               .select_related("artist")

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
                    "artist": match.artist.name,
                    "year": match.year,
                    "length": convert_seconds(match.length),
                    "artist_url": reverse("music:artist_detail", kwargs={"artist_uuid": match.artist.uuid})
                }
            )

        response = {
            "status": "OK",
            "song_list": song_list
        }

        return JsonResponse(response)


@login_required
def mark_song_as_listened_to(request, uuid):
    """
    Indicate that this song has been listened to, but only if we're in production
    """

    if not settings.DEBUG:
        song = Song.objects.get(user=request.user, uuid=uuid)
        song.listen_to()

    return JsonResponse(
        {
            "status": "OK"
        }
    )


@login_required
def get_song_id3_info(request):

    song = request.FILES["song"].read()
    id3_info = Song.get_id3_info(request, messages, song)
    return JsonResponse({**id3_info})


@method_decorator(login_required, name="dispatch")
class SearchTagListView(ListView):
    """
    Return a list of songs and albums which have a given tag
    """
    template_name = "music/tag_search.html"

    def get_queryset(self):
        tag_name = self.request.GET["tag"]

        return Song.objects.filter(
            user=self.request.user,
            tags__name=tag_name
        ).select_related(
            "artist"
        ).order_by(
            F("year").desc(nulls_last=True),
            "title"
        )

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

        album_list = []

        for match in Album.objects.filter(
                user=self.request.user,
                tags__name=self.request.GET["tag"]
        ).select_related(
            "artist"
        ).order_by("-year"):
            album_list.append(
                {
                    "uuid": match.uuid,
                    "title": match.title,
                    "artist": match.artist,
                    "year": match.year,
                }
            )

        return {
            **context,
            "tag_name": self.request.GET["tag"],
            "song_list": song_list,
            "album_list": album_list,
        }


@method_decorator(login_required, name="dispatch")
class PlaylistDetailView(DetailView):

    model = Playlist
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        obj_dict = model_to_dict(self.object)
        obj_dict["uuid"] = str(self.object.uuid)

        return {
            **context,
            "playlist_json": json.dumps(obj_dict)
        }


@method_decorator(login_required, name="dispatch")
class CreatePlaylistView(FormRequestMixin, CreateView):

    model = Playlist
    form_class = PlaylistForm
    template_name = "music/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def form_valid(self, form):

        playlist = form.save(commit=False)
        playlist.user = self.request.user

        playlist.parameters = {
            x: self.request.POST[x]
            for x in
            ["tag", "start_year", "end_year", "exclude_albums", "exclude_recent"]
            if x in self.request.POST and self.request.POST[x] != ""
        }
        playlist.save()

        if playlist.type != "manual":
            playlist.populate()

        self.success_url = reverse_lazy("playlist_detail", kwargs={"uuid": playlist.uuid})
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("music:playlist_detail", kwargs={"uuid": self.object.uuid})


@method_decorator(login_required, name="dispatch")
class UpdatePlaylistView(FormRequestMixin, UpdateView):

    model = Playlist
    form_class = PlaylistForm
    slug_field = "uuid"
    slug_url_kwarg = "playlist_uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tags"] = [{"text": x.name, "is_meta": x.is_meta} for x in self.object.tags.all()]
        return context

    def form_valid(self, form):
        playlist = form.save()

        # Deal with any changed parameters that could possibly
        #  refresh the song list.
        if playlist.type != "manual" and \
           (
               "size" in form.changed_data
               or self.request.POST.get("exclude_albums", "") != playlist.parameters.get("exclude_albums", "")
               or self.request.POST.get("exclude_recent", "") != playlist.parameters.get("exclude_recent", "")
           ):

            parameters = {
                x: self.request.POST[x]
                for x in
                ["start_year", "end_year", "exclude_albums", "exclude_recent"]
                if x in self.request.POST and self.request.POST[x] != ""
            }

            # We don't allow changing the tag, so it won't be included in
            #  the POST args. Add it here.
            if playlist.type == "tag":
                parameters["tag"] = playlist.parameters["tag"]

            playlist.parameters = parameters
            playlist.save()

            playlist.populate(refresh=True)

        messages.add_message(
            self.request, messages.INFO,
            "Playlist updated"
        )

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("music:playlist_detail", kwargs={'uuid': self.object.uuid})


@method_decorator(login_required, name="dispatch")
class PlaylistDeleteView(DeleteView):
    model = Playlist
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    # Verify that the user is the owner of the task
    def get_object(self, queryset=None):
        obj = super().get_object()
        if not obj.user == self.request.user:
            raise Http404
        return obj

    def get_success_url(self):
        messages.add_message(
            self.request,
            messages.INFO, f"Playlist <strong>{self.object.name}</strong> deleted",
        )
        return reverse("music:list")


@login_required
def get_playlist(request, uuid):

    playlist = Playlist.objects.get(uuid=uuid)

    song_list = []

    song_list = get_playlist_songs(playlist)

    total_time = humanize.precisedelta(
        timedelta(seconds=song_list["playtime"]),
        minimum_unit="minutes",
        format="%.f"
    )

    response = {
        "status": "OK",
        "totalTime": total_time,
        "playlistitems": song_list["song_list"]
    }

    return JsonResponse(response)


@login_required
def sort_playlist(request):
    """
    Given an ordered list of songs in a playlist, move a song to
    a new position within that playlist
    """

    playlistitem_uuid = request.POST["playlistitem_uuid"]
    new_position = int(request.POST["position"])

    playlistitem = PlaylistItem.objects.get(uuid=playlistitem_uuid)
    playlistitem.reorder(new_position)

    return JsonResponse({"status": "OK"}, safe=False)


@login_required
def search_playlists(request):

    playlists = Playlist.objects.filter(
        user=request.user,
        type="manual",
        name__icontains=request.GET.get("query", "")
    )

    return JsonResponse([{"value": x.name, "uuid": x.uuid} for x in playlists], safe=False)


@login_required
def add_to_playlist(request):
    """
    Add a song to a playlist
    """

    playlist_uuid = request.POST["playlist_uuid"]
    song_uuid = request.POST["song_uuid"]

    playlist = Playlist.objects.get(uuid=playlist_uuid)
    song = Song.objects.get(uuid=song_uuid)

    if PlaylistItem.objects.filter(playlist=playlist, song=song).exists():

        response = {
            "status": "Warning",
            "message": "That song is already on the playlist."
        }

    else:

        playlistitem = PlaylistItem(playlist=playlist, song=song)
        playlistitem.save()

        # Save the playlist in the user's session, so that this will
        #  be the default selection next time.
        request.session["music_playlist"] = playlist_uuid

        response = {
            "status": "OK"
        }

    return JsonResponse(response)


@login_required
def update_artist_image(request):
    """
    Update the image displayed on the artist detail page
    """

    artist_uuid = request.POST["artist_uuid"]
    image = request.FILES["image"]

    s3_client = boto3.client("s3")

    key = f"artist_images/{artist_uuid}"
    fo = io.BytesIO(image.read())
    s3_client.upload_fileobj(
        fo,
        settings.AWS_BUCKET_NAME_MUSIC,
        key,
        ExtraArgs={"ContentType": "image/jpeg"}
    )

    response = {
        "status": "OK"
    }

    return JsonResponse(response)


@login_required
def dupe_song_checker(request):
    """
    Given an artist name and song title, look for any
    possible duplicates.
    """

    artist = request.GET["artist"]
    title = request.GET["title"]

    song = Song.objects.filter(
        user=request.user,
        title__icontains=title,
        artist__name__icontains=artist
    ).select_related("album")

    if song:
        dupes = [
            {
                "title": x.title,
                "uuid": x.uuid,
                "url": Song.get_song_url(x),
                "note": x.note,
                "album_name": x.album.title if x.album else "",
                "album_url": reverse("music:album_detail", args=[x.album.uuid]) if x.album else "",
            }
            for x in
            song
        ]
    else:
        dupes = []

    return JsonResponse({"dupes": dupes})


@login_required
def missing_artist_images(request):
    """
    Temp view to return an artist without an image in S3
    """

    s3_resource = boto3.resource("s3")

    unique_uuids = {}

    paginator = s3_resource.meta.client.get_paginator("list_objects")
    page_iterator = paginator.paginate(Bucket="bordercore-music")

    for page in page_iterator:
        for key in page["Contents"]:
            m = re.search(r"^artist_images/(.*)", str(key["Key"]))
            if m:
                unique_uuids[m.group(1)] = True

    artists = Artist.objects.all(
    ).exclude(
        album__artist__name="Various"
    ).exclude(
        album__artist__name="Various Artists"
    ).order_by("?")

    for artist in artists:
        if str(artist.uuid) not in unique_uuids:
            return redirect(reverse(
                "music:artist_detail",
                kwargs={"artist_uuid": artist.uuid}
            ))

    return render(request, "music/index.html")


# @login_required
def recent_albums(request, page_number):
    """
    Get a list of recently added albums
    """
    recent_albums, paginator = get_recent_albums_service(request.user, page_number)
    response = {
        "status": "OK",
        "album_list": recent_albums,
        "paginator": paginator
    }

    return JsonResponse(response)
