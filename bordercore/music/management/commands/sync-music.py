"""
Management command to sync music files from S3 to the local filesystem.

This script supports syncing individual songs, entire directories, or album-based
tracks by extracting ID3 tags and organizing the files into a music directory
structure. It verifies that songs exist in the database before syncing and can
optionally run in dry-run mode.

Args:
    --uuid (str): The UUID of the song to download from S3.
    --directory (str): Directory containing songs to sync.
    --album-name (str): Album name for syncing.
    --file-name (str): Individual filename to sync.
    --artist (str): Artist name (overrides ID3 tag).
    --title (str): Song title (overrides ID3 tag).
    --sync-album-song (bool): Indicates that the song is part of an album.
    --song-uuid (str): The UUID of the song in the database.
    --dry-run (bool): Run without making changes.
"""

import os
import re
from argparse import ArgumentParser
from pathlib import Path
from typing import Any, Optional

import boto3
import mutagen
from colorama import Fore, Style
from mutagen.easyid3 import EasyID3

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models.query import QuerySet
from django.db.transaction import atomic

from music.models import Song

MUSIC_DIR = "/home/media/music"


class Command(BaseCommand):
    """
    Django management command to sync music files from S3 to local filesystem.

    This command supports downloading a song by UUID, syncing all songs in a directory,
    or syncing individual files. It reads metadata from ID3 tags or accepts overrides
    via command-line options. It verifies songs against the database before organizing
    and moving them into a structured local directory layout.
    """
    help = "Sync music from S3 to local filesystem"

    def add_arguments(self, parser: ArgumentParser) -> None:
        """
        Add custom arguments to the management command parser.

        Args:
            parser: Argument parser instance.
        """
        parser.add_argument(
            "--uuid",
            "-u",
            help="The UUID of the song to download",
        )
        parser.add_argument(
            "--directory",
            "-d",
            help="The directory of songs to sync",
        )
        parser.add_argument(
            "--album-name",
            "-l",
            help="The album name to sync",
        )
        parser.add_argument(
            "--file-name",
            "-f",
            help="The filename to sync",
        )
        parser.add_argument(
            "--artist",
            "-a",
            help="The song artist (overrides ID3 tag)",
        )
        parser.add_argument(
            "--title",
            "-t",
            help="The song title (overrides ID3 tag)",
        )
        parser.add_argument(
            "--sync-album-song",
            "-s",
            help="Sync a song as part of an album",
            action="store_true"
        )
        parser.add_argument(
            "--song-uuid",
            "-i",
            help="The song UUID",
        )
        parser.add_argument(
            "--dry-run",
            "-n",
            help="Dry run. Take no action",
            action="store_true"
        )

    @atomic
    def handle(self, *args: Any, album_name: Optional[str], artist: Optional[str], directory: Optional[str], file_name: Optional[str], title: Optional[str], uuid: Optional[str], song_uuid: Optional[str], **kwargs: Any) -> None:
        """
        Main entry point for the management command.

        Args:
            args: Additional positional arguments.
            album_name: Album name to sync.
            artist: Artist name override.
            directory: Directory path to sync.
            file_name: File path to sync.
            title: Song title override.
            uuid: UUID of song to download.
            song_uuid: Song UUID in the database.
            **kwargs: Additional arguments.
        """
        self.args = kwargs
        if uuid:
            self.download_from_s3(uuid)
        elif directory:
            self.sync_directory(directory, artist, album_name)
        elif file_name:
            self.sync_file(file_name, artist, title, album_name, song_uuid)
        else:
            self.stdout.write(f"  {Fore.YELLOW}No file or directory specified. Processing the current directory...{Style.RESET_ALL}")
            self.sync_directory(".", artist, album_name)

    def get_artist_dir(self, song: QuerySet[Song], artist: str, first_letter_dir: str) -> str:
        """
        Determine or create the directory for the given artist.

        Args:
            song: QuerySet of matching songs.
            artist: Name of the artist.
            first_letter_dir: First letter subdirectory.

        Returns:
            Path string to the artist directory.
        """
        song_obj = song.first()
        if song_obj is None:
            raise CommandError(f"   {Fore.RED}No song object found to determine artist directory.{Style.RESET_ALL}")

        if song_obj.first().album and song_obj.first().album.compilation:
            artist_dir = f"{MUSIC_DIR}/v/Various"
        else:
            artist_dir = f"{MUSIC_DIR}/{first_letter_dir}/{artist}"

        if not Path(artist_dir).is_dir():
            self.stdout.write(f"  {Style.DIM}Creating artist directory {artist_dir}{Style.RESET_ALL}")
            if not self.args["dry_run"]:
                Path(artist_dir).mkdir()

        return artist_dir

    def create_album_dir(self, artist_dir: str, album: str) -> None:
        """
        Create a directory for the album inside the artist's directory.

        Args:
            artist_dir: Directory of the artist.
            album: Album title.
        """
        album_dir = f"{artist_dir}/{album}"
        if not Path(album_dir).is_dir():
            self.stdout.write(f"  {Style.DIM}Creating album directory {artist_dir}/{album}{Style.RESET_ALL}")
            if not self.args["dry_run"]:
                Path(album_dir).mkdir()

    def get_file_path(self, artist_dir: str, album: Optional[str], track_number: Optional[str], title: str) -> str:
        """
        Construct the file path for the song based on context.

        Args:
            artist_dir: Artist directory.
            album: Album title.
            track_number: Song track number.
            title: Song title.

        Returns:
            Full path where the song will be saved.
        """
        if self.args["sync_album_song"]:
            path = f"{artist_dir}/{album}/{track_number} - {title}.mp3"
        else:
            path = f"{artist_dir}/{title}.mp3"

        return path

    def normalize_track_number(self, track_number: str) -> str:
        """
        Pad single-digit track numbers with a leading zero.

        Args:
            track_number: Original track number string.

        Returns:
            Normalized two-digit track number.
        """
        if len(track_number) == 1:
            return f"0{track_number}"
        return track_number

    def sanitize_filename(self, name: str) -> str:
        """
        Replace unsafe characters in filenames.

        Args:
            name: Raw name string.

        Returns:
            Sanitized name.
        """
        return name.replace("/", "-")

    def download_from_s3(self, uuid: str) -> None:
        """
        Download a song file from S3 using its UUID.

        Args:
            uuid: UUID of the song in S3.
        """

        song = Song.objects.get(uuid=uuid)
        if song.album:
            track_number = self.normalize_track_number(str(song.track))
            filename = f"{track_number} - {song.title}.mp3"
        else:
            filename = f"{song.title}.mp3"

        s3_client = boto3.client("s3")
        s3_client.download_file(settings.AWS_BUCKET_NAME_MUSIC, f"songs/{uuid}", filename)
        self.stdout.write(f"{Fore.GREEN}Downloading '{filename}'{Style.RESET_ALL}")

    def sanitize_tag(self, name: str) -> str:
        """
        Clean up ID3 tag values (e.g. remove '[Explicit]').

        Args:
            name: Raw tag value.

        Returns:
            Sanitized tag.
        """
        return name.replace(" [Explicit]", "")

    def get_id3_tag(self, tag_name: str, id3_info: dict, required: bool = True) -> Optional[str]:
        """
        Extract a tag value from ID3 metadata.

        Args:
            tag_name: The name of the ID3 tag.
            id3_info: Parsed ID3 metadata.
            required: Whether to raise an error if the tag is missing.

        Returns:
            Tag value if present, else None.

        Raises:
            CommandError: If the tag is required but missing.
        """

        if tag_name in id3_info:
            return self.sanitize_tag(id3_info[tag_name][0])
        if required:
            raise CommandError(f"Tag '{tag_name}' not found in file")
        return None

    def sync_directory(self, directory: str, artist: Optional[str], album_name: Optional[str]) -> None:
        """
        Sync all MP3 files in a directory.

        Args:
            directory: Path to directory to scan.
            artist: Optional override for artist.
            album_name: Optional override for album name.
        """

        if not Path(directory).is_dir():
            raise CommandError(f"{directory} is not a directory")

        pathlist = Path(directory).glob('**/*.mp3')
        for path in pathlist:
            self.sync_file(filename=str(path), artist=artist, title=None, album_name=album_name)

    def sync_file(self, filename: str, artist: Optional[str], title: Optional[str], album_name: Optional[str], song_uuid: Optional[str] = None) -> None:
        """
        Sync an individual song file by organizing and moving it to the correct path.

        Args:
            filename: Path to the MP3 file.
            artist: Optional artist name override.
            title: Optional song title override.
            album_name: Optional album name override.
            song_uuid: Optional UUID to match in the database.

        Raises:
            CommandError: If the song is not found or multiple matches exist.
        """

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
            album_name = self.get_id3_tag("album", id3_info, False)

        if self.args["sync_album_song"] and not album_name:
            raise CommandError("Album name not found in file or specified")

        if album_name:
            album_name = self.sanitize_filename(album_name)

        track_number = None
        if "tracknumber" in id3_info:
            track_number = id3_info["tracknumber"][0].split("/")[0]
            track_number = self.normalize_track_number(track_number)

        if self.args["sync_album_song"] and not track_number:
            raise CommandError("Track number not found in file")

        # For the first letter directory, use the first non-alphanumeric character.
        #  This handles edge cases like the band 'Til Tuesday
        if artist is None:
            raise CommandError("Artist name is required to compute first letter directory")

        first_letter_dir = re.sub(r"\W+", "", artist).lower()[0]

        if song_uuid:
            song = Song.objects.filter(uuid=song_uuid)
        else:
            song = Song.objects.filter(title=title, artist__name=artist)

        if self.args["sync_album_song"]:
            song.filter(album__title=album_name)

        # Verify that the song is in the database
        if not song.first():
            raise CommandError(f"  {Fore.RED}Song does not appear to exist in db, artist={artist}, title={title}{Style.RESET_ALL}")
        if len(song) > 1:
            raise CommandError(f"  {Fore.RED}More than one song found in the db.{Style.RESET_ALL}")
        self.stdout.write(f"  {Fore.GREEN}Song found in the db, uuid={song.first().uuid}{Style.RESET_ALL}")

        if title is None:
            raise CommandError(f"  {Fore.RED}Title is required to sanitize filename")

        title = self.sanitize_filename(title)
        artist = self.sanitize_filename(artist)

        artist_dir = self.get_artist_dir(song, artist, first_letter_dir)

        if self.args["sync_album_song"]:
            if album_name is None:
                raise CommandError(f"  {Fore.RED}Album name is required to create album directory")
            self.create_album_dir(artist_dir, album_name)

        path = self.get_file_path(artist_dir, album_name, track_number, title)

        if Path(path).is_file():
            self.stdout.write(f"  {Fore.RED}File is already synced: '{path}' Skipping...{Style.RESET_ALL}")
            return

        if not self.args["dry_run"]:
            os.rename(filename, path)

        self.stdout.write(f"  {Style.DIM}Moving song to {path}{Style.RESET_ALL}")
