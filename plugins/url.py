# coding=utf-8

import html.parser
import re
import urllib.request

DEFAULT_AGENT = 'Yui'

class TitleParser(html.parser.HTMLParser):
    def __init__(self):
        html.parser.HTMLParser.__init__(self)
        self.reading = False
        self.done = False
        self.title = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'title' and not self.done:
            self.reading = True

    def handle_endtag(self, tag):
        if tag == 'title':
            self.reading = False
            self.done = True

    def handle_data(self, data):
        if self.reading:
            self.title += data

    def handle_charref(self, ref):
        if self.reading:
            self.handle_entityref('#' + ref)

    def handle_entityref(self, ref):
        if self.reading:
            self.title += '&%s;' % ref


def urlEncodeNonAscii(string):
    return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), string)


# returns a properly encoded url (escaped unicode etc)
# or None if it's not a valid url
def get_encoded_url(url):
    # test if it's a valid URL and encode it properly, if it is
    parts = urllib.request.urlparse(url)
    if not ((parts[0] == 'http' or parts[0] == 'https') and parts[1] and parts[1] != 'localhost' and not
    parts[1].split('.')[-1].isdigit()):
        return None

    # handle unicode URLs
    url = urllib.request.urlunparse(
        p if i == 1 else urlEncodeNonAscii(p)
        for i, p in enumerate(parts)
    )
    return url


def get_url_title(url):
    enc = 'utf8'
    title = ''
    parser = TitleParser()
    try:
        headers = {
            'User-Agent': yui.config_val('httpUserAgent', default=DEFAULT_AGENT)
        }
        req = urllib.request.Request(url, data=None, headers=headers)
        resp = urllib.request.urlopen(req, timeout=5)

        # try the charset set in the html header first, if there is one
        if 'content-type' in resp.headers and 'charset=' in resp.headers['content-type']:
            enc = resp.headers['content-type'].split('charset=')[-1]

        # read up to 1mb
        chunk = resp.read(1024 * 1024)
        parser.feed(chunk.decode(enc))
        if parser.done:
            title = parser.title
        parser.close()
    except Exception as ex:
        return None
    else:
        if len(title) > 0:
            for e in enc:
                try:
                    dec = title.decode(e)
                    dec = parser.unescape(dec)
                    return dec
                except Exception as ex:
                    pass
        return title


@yui.event('msgRecv')
def url(msg, channel):
    # find urls in channel message
    words = msg.split(' ')
    titles = []
    maxUrls = 5
    foundTitle = False
    for w in words:
        url = get_encoded_url(w)
        if not url:
            continue

        maxUrls -= 1
        if maxUrls == 0:
            break

        title = get_url_title(url)
        if title:
            title = ' '.join(title.split())  # remove leading/trailing spaces, reduce repeated spaces to just one
            titles.append('"%s"' % title)
            foundTitle = True
        else:
            titles.append('[no title]')

    # don't say anything, if we couldn't get any titles
    if foundTitle:
        concat = ', '.join(titles)
        yui.send_msg(channel, concat)
