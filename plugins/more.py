# coding=utf-8

MAXSIZE = 5000  # max. amount of chars to keep per channel
TEXT = {}  # lines of text for .more
LINE = {}  # current line
LOCK = False


def chunks(l, chunk_size):
    for i in range(0, len(l), chunk_size):
        yield l[i:i + chunk_size]


@yui.event('pre_send')
def pre_send(msg, channel):
    if LOCK:
        return

    msg = msg[:MAXSIZE]
    spl = msg.split('\n')
    if len(spl) > 1:
        TEXT[channel] = spl
        LINE[channel] = 0
        return spl[0]

    enc = yui.encode(msg)
    if len(enc) > yui.safe_msg_bytes:
        TEXT[channel] = [yui.decode(e) for e in chunks(enc, yui.safe_msg_bytes)]
        LINE[channel] = 0
        return TEXT[channel][0]


@yui.command('more')
def more(channel):
    global LOCK
    LINE[channel] += 1
    n = LINE[channel]

    if n < len(TEXT[channel]):
        LOCK = True
        yui.send_msg(channel, TEXT[channel][n])
        LOCK = False
    else:
        return "<EOF>"
