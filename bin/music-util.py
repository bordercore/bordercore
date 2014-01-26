#!/usr/bin/env python
# encoding: utf-8

import getopt, logging, re, sys
from os import listdir, mkdir
from os.path import abspath, basename, isdir, isfile
from shutil import copy2

from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

from music.models import Song, Album, SongSource

MUSIC_ROOT = "/home/media/music"
songsource = "Amazon"
dry_run = False
operation = None
compilation = False

def info(song):
    try:

        audio = MP3(song, ID3=EasyID3)
        for key in audio:
            print "%s: %s" % (key, audio[key])
        print "length: %s" % audio.info.length
        print "sample_rate: %s" % audio.info.sample_rate
        print "bitrate: %s" % audio.info.bitrate
    except IOError as e:
        print "Error: %s (%s)" % (e.strerror, song)

def snarf_directory(directory):
    for filename in listdir(directory):
        if filename.lower().endswith(".mp3"):
            file_path = abspath("%s/%s" % (directory, filename))
            if isfile(file_path):
                snarf_file(file_path)


def snarf_file(song):

    logging.info("Snarfing %s", (song,))

    try:
        audio = MP3(song, ID3=EasyID3)

        tracknumber = None
        date = None
        a = None

        if 'tracknumber' in audio:
            tracknumber = audio.get('tracknumber', None)[0].split('/')[0]
        if 'date' in audio:
            date = audio.get('date')[0]
            r = re.compile('^\d\d\d\d')
            m = r.match(date)
            if m:
                date = m.group(0)

        if compilation:
            artist_name = 'Various'
        else:
            artist_name = audio.get('artist')[0]

        # Insert the metadata into the db
        # If the song doesn't have a date, then we can't lookup album info for it
        if date:
            a = Album.objects.filter(title__iexact=audio.get('album')[0]).filter(artist=artist_name).filter(year=date)
            if a:
                if len(a) > 1:
                    raise Exception ("multiple album matches found")
                if a[0].title != audio.get('album')[0]:
                    raise Exception ("album found, but case does not match ('%s' vs '%s')" %
                                     (a[0].title, audio.get('album')[0]))
            else:
                a = Album(title=audio.get('album')[0], artist=artist_name, year=date)
                a.save()

        source = SongSource.objects.get(name=songsource)

        s, created = Song.objects.get_or_create(artist=audio.get('artist')[0], title=audio.get('title')[0],
                                                year=date, source=source, track=tracknumber, album=a[0])

        if not created:
            logging.warning("Song already exists in db")

        s.length = audio.info.length
        s.save()

        # Move the song file to its final place

        # First create the directory structure, if necessary.
        # One for the artist and one for the album.
        for dirname in ("%s" % (artist_name,), "%s/%s" % (artist_name, audio.get('album')[0])):
            fulldirname = "%s/%s" % (MUSIC_ROOT, dirname)
            if not isdir(fulldirname):
                logging.info("Creating dir %s", fulldirname)
                mkdir(fulldirname)

        if len(tracknumber) == 1:
            tracknumber = '0' + tracknumber

        # We want to filename to be in this format:  <track> - <song>.mp3
        #   Check if the track number is already present
        p = re.compile("^(\d+) - ")
        filename = audio.get('title')[0]
        if not p.match(filename):
            filename = "%s - %s.mp3" % (tracknumber, filename)
        if basename(song) != filename:
            logging.warning("Input filename does not match output filename (%s vs %s)", basename(song), filename)

        # Copy the file
        destfilename = "%s/%s/%s/%s" % (MUSIC_ROOT, artist_name, audio.get('album')[0], filename)

        if isfile(destfilename):
            logging.warning("File already exists")
        else:
            copy2(song, destfilename)

        # If album artwork is not found, create it
        artwork_file = "%s/%s/%s/artwork.jpg" % (MUSIC_ROOT, artist_name, audio.get('album')[0])
        if not isfile(artwork_file):
            logging.info("Creating artwork for album")
            audio = MP3(destfilename)
            if 'APIC:' in audio.tags:
                artwork = audio.tags['APIC:']
                fh = open(artwork_file, "w")
                fh.write(artwork.data)
                fh.close()
            else:
                logging.error("Cannot find artwork in file %s", destfilename)

    except (IOError, OSError) as e:
        logging.error("Error: %s (%s)", e.strerror, song)

if __name__ == "__main__":

    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(levelname)s: %(message)s')

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:o:ns:f:i:d:c", ["ifile=","ofile="])
    except getopt.GetoptError:
        print 'test.py -i <inputfile> -o <outputfile>'
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print 'test.py -c -n -s <song>'
            sys.exit()
        elif opt in ("-n", "--dry-run"):
            dry_run = True
        elif opt in ("-i", "--info"):
            operation = 'info'
            song = arg
        elif opt in ("-f", "--snarf_file"):
            operation = 'snarf_file'
            song = arg
        elif opt in ("-d", "--snarf_directory"):
            operation = 'snarf_directory'
            directory = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
        elif opt in ("-s", "--source"):
            songsource = arg
        elif opt in ("-c", "--compilation"):
            compilation = True

    if operation == 'snarf_file':
        snarf_file(song)
    if operation == 'snarf_directory':
        snarf_directory(directory)
    elif operation == 'info':
        info(song)


