import datetime
from icalendar import Calendar, Event
from dateutil.parser import parse
from dateutil.tz import tzlocal, tzutc
from lxml import html
import requests

cal = Calendar()
cal.add('x-wr-calname', "Vilnius Hardcore events")
cal.add('version', '2.0')
cal.add('prodid', '-//hcevents//wemakethings.net//')

page = requests.get('http://hardcore.lt').text
#page = open('index.html').read()

tree = html.fromstring(page)
for event_element in tree.xpath('//ol[@class="ai1ec-date-events"]'):
    link = event_element.xpath('li[@class="ai1ec-date"]/a')[0]
    title = link.text.strip()
    url = link.get('href')
    time_str = event_element.xpath('li[@class="ai1ec-date"]/p/span[@class="ai1ec-event-time"]/text()')[0].strip()
    time = parse(time_str).replace(tzinfo=tzlocal())

    description_elements = event_element.xpath('li[@class="ai1ec-date"]/following-sibling::*')
    description_html = ''.join(html.tostring(e).decode('utf-8') for e in description_elements).strip()
    description_text = '\n'.join(e.text_content().strip() for e in description_elements).strip()
    description_text += '\n' + url

    if not title:
        title = description_text.split('\n')[0]
    print(title)

    # Events end next day at 4 in the morning.
    endtime = (time + datetime.timedelta(days=1)).replace(hour=4, minute=0, second=0)

    cal_event = Event()
    cal_event.add('uid', url)
    cal_event.add('dtstart', time.astimezone(tzutc()))
    cal_event.add('dtend', endtime.astimezone(tzutc()))
    cal_event.add('dtstamp', datetime.datetime.now(tzutc()))
    cal_event.add('summary', title)
    cal_event.add('description', description_text)
    cal_event.add('x-alt-desc', description_html, parameters={'fmttype': 'text/html'})
    cal.add_component(cal_event)


with open('hcevents.ics', 'wb') as f:
    f.write(cal.to_ical())
