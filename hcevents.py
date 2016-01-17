#!/usr/bin/env python3
import datetime
from dateutil.parser import parse
from dateutil.tz import tzlocal, tzutc
from lxml import html
import requests
import collections
import icalendar
import PyRSS2Gen as RSS2
import pickle


Event = collections.namedtuple("Event", [
    "title",
    "url",
    "time",
    "description_html",
    "description_text"
])


def get_events():
    page = requests.get('http://hardcore.lt').text
    tree = html.fromstring(page)
    events = []
    for event_element in tree.xpath('//ol[@class="ai1ec-date-events"]'):
        link = event_element.xpath('li[@class="ai1ec-date"]/a')[0]
        title = link.text.strip()
        url = link.get('href')
        time_str = event_element.xpath('descendant-or-self::span[@class="ai1ec-event-time"]/text()')[0].strip()
        time = parse(time_str).replace(tzinfo=tzlocal())

        description_elements = event_element.xpath('li[@class="ai1ec-date"]/following-sibling::*')
        description_html = ''.join(html.tostring(e).decode('utf-8') for e in description_elements).strip()
        description_text = '\n'.join(e.text_content().strip() for e in description_elements).strip()
        description_text += '\n' + url

        if not title:
            title = description_text.split('\n')[0]

        events.append(Event(
            title=title,
            url=url,
            time=time,
            description_html=description_html,
            description_text=description_text
        ))

    return events


def output_calendar(filename, events):
    cal = icalendar.Calendar()
    cal.add('x-wr-calname', "Vilnius Hardcore events")
    cal.add('version', '2.0')
    cal.add('prodid', '-//hcevents//wemakethings.net//')
    for event in events:
        # Events end next day at 4 in the morning.
        endtime = (event.time + datetime.timedelta(days=1)).replace(hour=4, minute=0, second=0)
        cal_event = icalendar.Event()
        cal_event.add('uid', event.url)
        cal_event.add('dtstart', event.time.astimezone(tzutc()))
        cal_event.add('dtend', endtime.astimezone(tzutc()))
        cal_event.add('dtstamp', datetime.datetime.now(tzutc()))
        cal_event.add('summary', event.title)
        cal_event.add('description', event.description_text)
        cal_event.add('x-alt-desc', event.description_html, parameters={'fmttype': 'text/html'})
        cal.add_component(cal_event)
    with open(filename, 'wb') as f:
        f.write(cal.to_ical())


def output_rss(filename, events):
    items = []
    try:
        with open('pubdates.pickle', 'rb') as f:
            pubdates = pickle.load(f)
    except (FileNotFoundError, EOFError):
        pubdates = {}
    updated_pubdates = {}
    for event in events:
        if event in pubdates:
            pubdate = pubdates[event]
        else:
            pubdate = datetime.datetime.now(tzlocal())
        updated_pubdates[event] = pubdate
        items.append(RSS2.RSSItem(
            title = "{:%Y-%m-%d} {}".format(event.time, event.title),
            link = event.url,
            guid = RSS2.Guid(event.url),
            pubDate = pubdate,
            description = "{:%Y-%m-%d %H:%M}\n{}".format(event.time, event.description_html)
        ))
    with open('pubdates.pickle', 'wb') as f:
        pickle.dump(updated_pubdates, f)
    rss = RSS2.RSS2(
        title = "Vilnius Hardcore events",
        link = "http://wemakethings.net/hcevents/",
        lastBuildDate = max(updated_pubdates.values()),
        description = '',
        items = items
    )
    with open(filename, 'wb') as f:
        rss.write_xml(f)

if __name__ == "__main__":
    events = get_events()
    output_calendar("hcevents.ics", events)
    output_rss("hcevents.xml", events)
