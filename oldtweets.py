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
import twitter
import sys
import getopt
import math


help_message = '''
oldtweets.py - backup or delete your older tweets
Based on a script by David Larlet @davidbgk


** run it to see the output
cat credentials | ./oldtweets.py

** Want to backup?
cat credentials | ./oldtweets.py >> mytweetsbackupfile.txt
(your oldest tweets will be at the top)

** Want to delete old tweets?
cat credentials | ./oldtweets.py --delete

** Want to backup and delete?
cat credentials | ./oldtweets.py --delete >> mytweetsbackupfile.txt

** By default, the script will ignore the latests 200 tweets. Want to choose another number (will be rounded down to the closest hundred)
cat credentials | ./oldtweets.py --delete --keep=100 >> mytweetsbackupfile.txt

'''


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def main(argv=None):
    option_delete = 0
    keep_number = 200
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "h:v", ["delete", "help", "keep="])
        except getopt.error, msg:
            raise Usage(msg)

        # option processing
        for option, value in opts:
            # if option == "-v":
            #     verbose = True
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option == "--delete":
                option_delete = 1
            if option == "--keep":
                try:
                    keep_number = int(value)
                except:
                    raise Usage("Value of --keep must be a number. Ideally a multiple of 100")

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

    tweets_ids = []
    tweets_len = 0
    min_page = int(math.floor(keep_number / 100))
    for i in range(min_page, min_page + 30):  # limiting to approximately 3000 API calls...
        tweets_ids += [status.id for status in api.GetUserTimeline(page=i + 1, count=100)]
        # print i, tweets_ids, len(tweets_ids)
        if tweets_len == len(tweets_ids):  # haven't received anything new, we're at the end of the list. stop here
            break
        else:
            tweets_len = len(tweets_ids)
            # wait a bit, throttled api - The API limits 350 calls per hours. so 1 call every 10.28 seconds
            time.sleep(11)

    # output tweets, delete on demand
    for tweet_id in tweets_ids[::-1]:
        # verify
        print "Tweet id: ", tweet_id, " --  Date: ", api.GetStatus(tweet_id).created_at, " || ", api.GetStatus(tweet_id).text.encode('utf-8')
        # delete
        if option_delete == 1:
            status = api.DestroyStatus(tweet_id)
        # wait a bit, throttled api - The API limits 350 calls per hours. so 1 call every 10.28 seconds
        time.sleep(11)


if __name__ == "__main__":
    sys.exit(main())
