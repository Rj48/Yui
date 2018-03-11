# coding = utf-8

import re
import humanize
import requests
from PIL import Image
from io import BytesIO

HOST = yui.config_val('jpg', 'host', default='https://x0.at/')
MAX_SIZE = yui.config_val('jpg', 'maxSize', default=20 * 1024 * 1024)
QUALITY = yui.config_val('jpg', 'quality', default=70)
RESIZE = yui.config_val('jpg', 'resize', default=1024)
TIMEOUT = yui.config_val('jpg', 'timeout', default=60)
TYPE_RE = re.compile('image/.*')


@yui.threaded
@yui.command('jpg', 'jpeg')
def jpeg(argv):
    """Resize/compress an image. Usage: jpg <url> [quality] [size]"""
    qual = QUALITY
    resize = RESIZE
    if len(argv) < 2:
        return
    if len(argv) > 2:
        qual = int(argv[2])
    if len(argv) > 3:
        resize = int(argv[3])

    req = requests.get(argv[1], stream=True, timeout=TIMEOUT)

    clen = int(req.headers.get('Content-Length', 0))
    if clen > MAX_SIZE:
        return 'Content-Length {} too big'.format(clen)

    ctype = req.headers.get('Content-Type')
    if not TYPE_RE.fullmatch(ctype):
        return 'Content-Type "{}" not supported'.format(ctype)

    data = BytesIO()
    size = 0
    chunk_size = 1024 ** 2
    for chunk in req.iter_content(chunk_size):
        size += len(chunk)
        if size > MAX_SIZE:
            return 'Content too large'
        data.write(chunk)

    img = Image.open(data)
    img.thumbnail((resize, resize), Image.ANTIALIAS)
    data = BytesIO()
    img.save(data, "JPEG", optimize=True, quality=qual)
    size = data.tell()
    data.seek(0)

    try:
        req = requests.post(HOST, files={'file': ('needsmore.jpg', data)})
        if req.text.startswith('http'):
            return '{} ({})'.format(req.text, humanize.naturalsize(size))
    except:
        pass
    return 'Something went wrong while uploading :('

