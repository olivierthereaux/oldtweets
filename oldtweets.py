#!/usr/bin/env python
# encoding: utf-8
"""
READ ME FIRST!

This script is a way to back up (and delete, if you so desire) all your tweets beyond the latest 100

This script will work if, and only if, you:

1/ Install python-twitter: http://code.google.com/p/python-twitter/ and dependencies
2/ go to dev.twitter.com, sign up with your account and create a new app (the details can be bogus, your app will be private)
3/ copy the consumer key and secret from your app in a credentials file
4/ go to "my access token" in the (righthand) menu of your app and copy the token and key in a credentials file
(a credentials file is distributed with this script, as a sample)

"""

import time
import datetime
import twitter
import sys
import getopt
import math


help_message = '''
oldtweets.py - backup and delete your tweets older than 4 weeks ago
Based on a script by David Larlet @davidbgk


* dry-run to see all tweets older than 4 weeks

    cat credentials | ./oldtweets.py --dry-run

* print *and delete from twitter* tweets older than 4 weeks (your oldest tweets will be at the top)

    cat credentials | ./oldtweets.py >> mytweetsbackupfile.txt

* [FIXME] The tweets can still sometimes output in the wrong order, with some duplicates.

    cat credentials | ./oldtweets.py | sort | uniq >> mytweetsbackupfile.txt


'''


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def main(argv=None):
    option_delete = 1 #unless you use --dry-run, we're deleting
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "h", ["help", "dry-run"])
        except getopt.error, msg:
            raise Usage(msg)

        # option processing
        for option, value in opts:
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option == "--dry-run":
                option_delete = 0

    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 2
    consumer_key = ''
    consumer_secret = ''
    access_token_key = ''
    access_token_secret = ''

    for line in sys.stdin.readlines():
        params = line.split()
        if len(params) == 2:
            if params[0] == "consumer_key":
                consumer_key = params[1]
            if params[0] == "consumer_secret":
                consumer_secret = params[1]
            if params[0] == "access_token_key":
                access_token_key = params[1]
            if params[0] == "access_token_secret":
                access_token_secret = params[1]

    api = twitter.Api(consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token_key=access_token_key,
        access_token_secret=access_token_secret)

    statuses = list()
    latest_tweet = None
    timeline_page = 0
    thereismore = 1
    
    
    # get all the tweets
    while thereismore:
        add_statuses = api.GetUserTimeline(count=200, include_rts=True, page=timeline_page)
        if len(add_statuses) > 0:
            statuses = statuses + add_statuses
            timeline_page = timeline_page+1
        else:
            thereismore = 0
        time.sleep(1)

    start_delete_at = None
    
    # discard tweets posted between now and 4 weeks ago
    fourweeksago = datetime.date.today()-datetime.timedelta(28)
    while start_delete_at == None:
        status = statuses.pop(0)
        status_created_at = datetime.datetime.strptime(status.created_at, "%a %b %d %H:%M:%S +0000 %Y")
        if datetime.date(status_created_at.year, status_created_at.month, status_created_at.day) < fourweeksago:
            start_delete_at = status.id

    for tweet in statuses[::-1]:
        status_created_at = datetime.datetime.strptime(tweet.created_at, "%a %b %d %H:%M:%S +0000 %Y")
        # [FIXME] Making sure not to delete new stuff, which for some odd reason seems to be necessary
        if datetime.date(status_created_at.year, status_created_at.month, status_created_at.day) < fourweeksago:
            tweet_text = tweet.text.replace('\n', '').replace('\r', '')
            print "Tweet id: ", tweet.id, " --  Date: ", tweet.created_at, " || ", tweet_text.encode('utf-8')
            # delete
            if option_delete == 1:
                try:
                    status = api.DestroyStatus(tweet.id)
                    # wait a bit, throttled api.
                    time.sleep(2)
                except Exception, e:
                    pass


if __name__ == "__main__":
    sys.exit(main())
