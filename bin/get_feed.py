#!/usr/bin/env python
# encoding: utf-8

import codecs
import datetime
import exceptions
import feedparser
import psycopg2
import sys
import xml.sax.saxutils as saxutils

import dtuple
import requests

LOG_FILE = "/home/www/logs/get_feed.log"
RDF_DIR = "/home/www/htdocs/bordercore/rdf"

def update_feeds(feed_id=None):

    conn = psycopg2.connect("dbname=django host=localhost user=bordercore password=4locus2")
    cursor = conn.cursor()

    # If an argument is supplied on the command line, interpret that as the
    #  feed id to update.  Otherwise update all feeds.
    sql = "SELECT id, name, url FROM feed_feed"
    if feed_id:
        sql = sql + " WHERE id = %d" % int(feed_id)

    cursor.execute(sql)
    descr = dtuple.TupleDescriptor(cursor.description)

    rows = cursor.fetchall()
    for row in rows:
        row = dtuple.DatabaseTuple(descr, row)

        r = requests.get(row.url)

        try:

            if r.status_code != 200:
                r.raise_for_status()

            # Store a copy of the raw RDF for debugging
            raw_file = codecs.open(RDF_DIR + "/%d.xml" % row.id, 'w', 'utf-8')
            raw_file.write(r.text)
            raw_file.close()

            d = feedparser.parse(r.text)

            cursor.execute("DELETE FROM feed_feeditem WHERE feed_id = %s", (row.id,))

            for x in d.entries:
                title = x.title or 'No Title'
                link = x.link or ''
                cursor.execute("INSERT INTO feed_feeditem (feed_id, title, link, created) VALUES (%s, %s, %s, now())", (row.id, saxutils.unescape(title), saxutils.unescape(link)))

        except Exception as e:

            message = ""
            if isinstance(e, requests.exceptions.HTTPError):
                message = e
            elif isinstance(e, psycopg2.Error):
                message = e.pgerror
            elif isinstance(e, exceptions.UnicodeEncodeError):
                message = str(type(e)) + ': ' + str(e)
            else:
                message = e

            t = datetime.datetime.now()
            log_file = open(LOG_FILE, 'a')
            log_file.write("%s Exception for %s (feed_id %d): %s\n" % (t.strftime('%Y-%m-%d %H:%M:%S'), row.name, row.id, message))
            log_file.close()

        finally:

            cursor.execute("UPDATE feed_feed SET last_response_code = %s, last_check = NOW() WHERE id = %s", (r.status_code, row.id))
            conn.commit()


if __name__=="__main__":

    if len(sys.argv) == 2:
        feed_id = sys.argv[1]
    else:
        feed_id = None

    update_feeds(feed_id)
