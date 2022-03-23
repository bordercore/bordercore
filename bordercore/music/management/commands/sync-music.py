import os
import re
from pathlib import Path

import boto3
import mutagen
from colorama import Fore, Style
from mutagen.easyid3 import EasyID3

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.transaction import atomic

from music.models import Song

MUSIC_DIR = "/home/media/music"


class Command(BaseCommand):
    help = "Sync music from S3 to local filesystem"

    def add_arguments(self, parser):
        parser.add_argument(
            "--uuid",
            help="The UUID of the song to download",
        )
        parser.add_argument(
            "--directory",
            help="The directory of songs to sync",
        )
        parser.add_argument(
            "--album-name",
            help="The album name to sync",
        )
        parser.add_argument(
            "--file-name",
            help="The filename to sync",
        )
        parser.add_argument(
            "--artist",
            help="The song artist (overrides ID3 tag)",
        )
        parser.add_argument(
            "--title",
            help="The song title (overrides ID3 tag)",
        )
        parser.add_argument(
            "--sync-album-song",
            help="Sync a song as part of an album",
            action="store_true"
        )
        parser.add_argument(
            "--dry-run",
            help="Dry run. Take no action",
            action="store_true"
        )

    @atomic
    def handle(self, *args, album_name, artist, directory, file_name, title, uuid, **kwargs):

        self.args = kwargs
        if uuid:
            self.download_from_s3(uuid)
        elif directory:
            self.sync_directory(directory, album_name)
        else:
            self.sync_file(file_name, artist, title, album_name)

    def get_artist_dir(self, song, artist, first_letter_dir):
        if song.first().album and song.first().album.compilation:
            artist_dir = f"{MUSIC_DIR}/v/Various"
        else:
            artist_dir = f"{MUSIC_DIR}/{first_letter_dir}/{artist}"

        if not Path(artist_dir).is_dir():
            self.stdout.write(f"  {Style.DIM}Creating artist directory {artist_dir}{Style.RESET_ALL}")
            if not self.args["dry_run"]:
                Path(artist_dir).mkdir()

        return artist_dir

    def create_album_dir(self, artist_dir, album):
        album_dir = f"{artist_dir}/{album}"
        if not Path(album_dir).is_dir():
            self.stdout.write(f"  {Style.DIM}Creating album directory {artist_dir}/{album}{Style.RESET_ALL}")
            if not self.args["dry_run"]:
                Path(album_dir).mkdir()

    def get_file_path(self, artist_dir, album, track_number, song, title):
        if self.args["sync_album_song"]:
            path = f"{artist_dir}/{album}/{track_number} - {title}.mp3"
        else:
            path = f"{artist_dir}/{title}.mp3"

        return path

    def normalize_track_number(self, track_number):

        if len(track_number) == 1:
            return f"0{track_number}"
        else:
            return track_number

    def sanitize_filename(self, name):
        return name.replace("/", "-")

    def download_from_s3(self, uuid):

        song = Song.objects.get(uuid=uuid)
        if song.album:
            track_number = self.normalize_track_number(str(song.track))
            filename = f"{track_number} - {song.title}.mp3"
        else:
            filename = f"{song.title}.mp3"

        s3_client = boto3.client("s3")
        s3_client.download_file(settings.AWS_BUCKET_NAME_MUSIC, f"songs/{uuid}", filename)
        self.stdout.write(f"{Fore.GREEN}Downloading '{filename}'{Style.RESET_ALL}")

    def get_id3_tag(self, tag_name, id3_info, required=True):

        if tag_name in id3_info:
            return id3_info[tag_name][0]
        elif required:
            raise CommandError(f"Tag '{tag_name}' not found in file")

    def sync_directory(self, directory, album_name):

        if not Path(directory).is_dir():
            raise CommandError(f"{directory} is not a directory")

        pathlist = Path(directory).glob('**/*.mp3')
        for path in pathlist:
            self.sync_file(filename=str(path), artist=None, title=None, album_name=album_name)

    def sync_file(self, filename, artist, title, album_name):

        try:
            id3_info = EasyID3(filename)
        except mutagen.id3._util.ID3NoHeaderError:
            id3_info = {}

        self.stdout.write(f"{Fore.GREEN}Syncing '{filename}'{Style.RESET_ALL}")

        if not artist:
            artist = self.get_id3_tag("artist", id3_info)

        if not title:
            title = self.get_id3_tag("title", id3_info)

        if not album_name:
            album = self.get_id3_tag("album", id3_info, False)

        if self.args["sync_album_song"] and not album:
            raise CommandError("Album name not found in file or specified")

        if album:
            album = self.sanitize_filename(album)

        if "tracknumber" in id3_info:
            track_number = id3_info["tracknumber"][0].split("/")[0]
            track_number = self.normalize_track_number(track_number)

        if self.args["sync_album_song"] and not track_number:
            raise CommandError("Track number not found in file")

        # For the first letter directory, use the first non-alphanumeric character.
        #  This handles edge cases like the band 'Til Tuesday
        first_letter_dir = re.sub(r"\W+", "", artist).lower()[0]

        song = Song.objects.filter(title=title, artist__name=artist)

        if self.args["sync_album_song"]:
            song.filter(album__title=album)

        # Verify that the song is in the database
        if not song.first():
            raise CommandError(f"  {Fore.RED}Song does not appear to exist in db, artist={artist}, title={title}{Style.RESET_ALL}")
        elif len(song) > 1:
            raise CommandError(f"  {Fore.RED}More than one song found in the db.{Style.RESET_ALL}")
        else:
            self.stdout.write(f"  {Fore.GREEN}Song found in the db, uuid={song.first().uuid}{Style.RESET_ALL}")

        title = self.sanitize_filename(title)
        artist = self.sanitize_filename(artist)

        artist_dir = self.get_artist_dir(song, artist, first_letter_dir)

        if self.args["sync_album_song"]:
            self.create_album_dir(artist_dir, album)

        path = self.get_file_path(artist_dir, album, track_number, song, title)

        if Path(path).is_file():
            self.stdout.write(f"  {Fore.RED}File is already synced: '{path}' Skipping...{Style.RESET_ALL}")
            return

        if not self.args["dry_run"]:
            os.rename(filename, path)

        self.stdout.write(f"  {Style.DIM}Moving song to {path}{Style.RESET_ALL}")
