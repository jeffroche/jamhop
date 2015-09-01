import datetime
import logging
import os
import requests
import time


logger = logging.getLogger(__name__)

API_KEY = os.environ['LASTFM_KEY']


def top_albums(userid, target_date, charts=None):
    url = 'http://ws.audioscrobbler.com/2.0/?method=user.getweeklyalbumchart'
    charts = charts or chart_list(userid)
    for c in charts:
        if c['from_date'] == target_date or (
                target_date > c['from_date'] and target_date < c['to_date']):
            # Start date is either at the beginning or within the range
            logger.debug("For target %s, s:%s e:%s" % (target_date,
                                                       c['from_date'],
                                                       c['to_date']))
            break
    else:
        raise LastFMException("No chart for that range")
    params = {
        'user': userid,
        'from': c['from'],
        'to': c['to'],
        'api_key': API_KEY,
        'format': 'json'
    }
    resp = requests.get(url, params)
    r = resp.json()
    if 'error' in r:
        print r['error']
        raise LastFMException(r['message'])
    if 'weeklyalbumchart' not in r:
        return []
    results = []
    for album in r['weeklyalbumchart']['album'][:10]:
        results.append({'artist': album['artist']['#text'],
                        'album': album['name']})
    return results


def chart_list(userid):
    url = 'http://ws.audioscrobbler.com/2.0/?method=user.getweeklychartlist'
    params = {
        'user': userid,
        'api_key': API_KEY,
        'format': 'json'
    }
    resp = requests.get(url, params)
    r = resp.json()
    if 'weeklychartlist' not in r and 'chart' not in r['weeklychartlist']:
        return []
    charts = []
    for chart in r['weeklychartlist']['chart']:
        charts.append({
            'from': chart['from'],
            'to': chart['to'],
            'from_date': timestamp_to_date(chart['from']),
            'to_date': timestamp_to_date(chart['to']),
        })
    return charts


def dt_to_timestamp(dt):
    return time.mktime(dt.timetuple())


def timestamp_to_date(ts):
    dt = datetime.datetime.fromtimestamp(float(ts))
    return dt.date()


class LastFMException(Exception):
    pass
