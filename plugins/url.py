# coding=utf-8

import html.parser
import re
import urllib.error
import urllib.parse
import urllib.request
from time import time
import dateutil.parser

import socks
from sockshandler import SocksiPyHandler

USER_AGENT = yui.config_val('url', 'httpUserAgent', default='Yui')
PROXY_HOST = yui.config_val('url', 'socksProxyHost')
PROXY_PORT = yui.config_val('url', 'socksProxyPort')
PROXY_REGEX = yui.config_val('url', 'socksProxyRegex')

URLCACHE = {}  # url -> info cache


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

    def error(self, message):
        pass


def humanify(num):
    pre = ['KiB', 'MiB', 'GiB', 'TiB']
    if num < 1024:
        return '%d Byte' % num
    num /= 1024
    for p in pre:
        div = num / 1024
        if div < 1.0:
            return '%.2f%s' % (num, p)
        num = div


# quote a query string
def quote_qs(qs):
    parts = urllib.parse.parse_qs(qs, keep_blank_values=True)
    return '&'.join([
        urllib.parse.quote(p) + '=' + urllib.parse.quote(v[0]) if v
        else urllib.parse.quote(p)
        for p, v in parts.items()])


# returns a properly encoded url (escaped unicode etc)
# or None if it's not a valid url
def get_encoded_url(url):
    # test if it's a valid URL and encode it properly, if it is
    parts = urllib.request.urlparse(url)
    if not ((parts[0] == 'http' or parts[0] == 'https')
            and parts[1]
            and parts[1] != 'localhost'
            and not parts[1].split('.')[-1].isdigit()):
        return None

    # handle unicode URLs
    url = urllib.request.urlunparse(
        p if i == 1
        else quote_qs(p) if i == 4
        else urllib.parse.quote(p)
        for i, p in enumerate(parts)
    )
    return url


def get_url_title(url):
    enc = ['utf8', 'iso-8869-1', 'shift-jis']
    title = ''
    headers = {
        'User-Agent': USER_AGENT
    }
    try:
        req = urllib.request.Request(url, data=None, headers=headers)

        host = urllib.request.urlparse(url).netloc.split(':')[0]

        if PROXY_HOST and PROXY_PORT and re.match(PROXY_REGEX, host):
            opener = urllib.request.build_opener(SocksiPyHandler(socks.SOCKS5, PROXY_HOST, PROXY_PORT))
            resp = opener.open(req, timeout=5)
        else:
            resp = urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError as e:
        return 'Status: ' + str(e.code)
    except urllib.error.URLError as e:
        return 'Error: ' + str(e.reason)
    except Exception as e:
        return

    # get the site's title, only in html content
    if 'content-type' in resp.headers and 'html' in resp.headers['content-type']:
        # try the charset set in the html header first, if there is one
        if 'charset=' in resp.headers['content-type']:
            enc = enc + [resp.headers['content-type'].split('charset=')[-1]]

        # read up to 1mb
        chunk = resp.read(1024 * 1024)
        parser = TitleParser()
        for e in enc:
            try:
                decoded_chunk = chunk.decode(e, 'ignore')
                parser.feed(decoded_chunk)
                if parser.done:
                    title = parser.title
                parser.close()
                if len(title) > 0:
                    esc = parser.unescape(title)
                    return 'Title: ' + esc.strip()
            except Exception as ex:
                pass

    # no title, try to output some other useful data
    info = []
    if 'content-type' in resp.headers:
        info.append('Type: ' + resp.headers['content-type'].split(';')[0])
    if 'content-length' in resp.headers:
        info.append('Size: ' + humanify(int(resp.headers['content-length'])))
    if 'last-modified' in resp.headers:
        d = resp.headers['last-modified']
        try:
            parsed_date = dateutil.parser.parse(d)
            d = parsed_date.strftime('%F %T') + ' ' + parsed_date.tzname()
        except ValueError:
            pass
        info.append('Modified: ' + d)

    return ', '.join(info)


@yui.event('pre_recv')
def url(msg, channel):
    # find urls in channel message
    words = msg.split()
    titles = []
    max_urls = 3
    for w in words:
        enc_url = get_encoded_url(w)
        if not enc_url:
            continue

        if enc_url in URLCACHE and URLCACHE[enc_url]['timestamp'] > (time() - 60 * 60):
            title = URLCACHE[enc_url]['title']
        else:
            title = get_url_title(enc_url).strip()
            URLCACHE[enc_url] = {
                'timestamp': time(),
                'title': title
            }

        if title:
            titles.append(title)

        if len(titles) >= max_urls:
            break

    # don't say anything, if we couldn't get any titles
    if len(titles) > 0:
        concat = ' \x035|\x03 '.join(titles)
        yui.send_msg(channel, concat)
