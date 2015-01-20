# -*- coding: utf-8 -*-

import settings as settings
from rain import Measurement
import twitter
import random
import settings
import time


def twitter_api():
    """
    Returns an API handle for twitter
    """
    return twitter.Api(consumer_key=settings.CONSUMER_KEY,
                      consumer_secret=settings.CONSUMER_SECRET,
                      access_token_key=settings.ACCESS_TOKEN,
                      access_token_secret=settings.ACCESS_TOKEN_SECRET)


def tweet_status(rain, snow):
    """
    Tweets about rain/snow
    """
    # api = twitter_api()

    # print api.VerifyCredentials()

    tried = []
    #twitter doesn't allow posting the same message twice so we'll just 5x with different messages
    #FIXME: save message to JSON
    for i in range(0,5):
        try:
            if rain:
                if snow:
                    message = random.choice(settings.SNOW_MESSAGES)
                else:
                    message = random.choice(settings.RAIN_MESSAGES)
            else:
                if snow:
                    message = random.choice(settings.NO_SNOW_MESSAGES)
                else:
                    message = random.choice(settings.NO_RAIN_MESSAGES)

            if message in tried:
              continue

            send_tweet(message)
            break

        except Exception, e:
            print e
            tried.append(message)
            pass


def send_tweet(message, api=None):

    if not api:
        api = twitter_api()

    return api.PostUpdate(message)


