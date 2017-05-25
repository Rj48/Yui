import re
from collections import deque

JPN_RANGES = [
    (0x3000, 0x303f),
    (0x3040, 0x309f),
    (0x30a0, 0x30ff),
    (0xff00, 0xff21),
    (0xff3b, 0xff40),
    (0xff5b, 0xffef),
    (0x4e00, 0x9faf)]

SYMBOLS_RANGES = [
    (0x0, 0x40),
    (0x5b, 0x60),
    (0x7b, 0x7f)]

ALLOWED = JPN_RANGES + SYMBOLS_RANGES

MIN_ALLOWED_PERCENT = 0.5

PERCENTAGES = {}

ACTIVE_CHANNELS = []


def is_allowed(char):
    for r in ALLOWED:
        if r[0] <= ord(char) <= r[1]:
            return True
    return False


def chars_allowed(string):
    a = 0
    for c in string:
        if is_allowed(c):
            a += 1
    return a


def is_word(word):
    return re.search('^https?://', word) is None  # don't consider links spoken language


def overall_percent(nick):
    chars = 0
    allowed = 0
    for t in PERCENTAGES[nick]:
        chars += t[0]
        allowed += t[1]
    return allowed/chars


@yui.event('msgRecv')
def recv(channel, user, msg):
    global PERCENTAGES
    if channel not in ACTIVE_CHANNELS:
        return

    key = channel+user.nick
    if key not in PERCENTAGES.keys():
        PERCENTAGES[key] = deque([(50, 50)] * 10, 3)

    msg = ''.join([w for w in msg.split() if is_word(w)])
    if len(msg) < 1:
        return

    a = chars_allowed(msg)
    PERCENTAGES[key].appendleft((len(msg), a))

    if overall_percent(key) < MIN_ALLOWED_PERCENT:
        yui.kick(channel, user.nick, '日本語でおk')
        PERCENTAGES.pop(key)


@yui.admin
@yui.command('jpnordie')
def switch(channel):
    """Switch jpnordie on/off for the current channel."""
    if channel not in ACTIVE_CHANNELS:
        ACTIVE_CHANNELS.append(channel)
        return '頑張ってね o/'
    else:
        ACTIVE_CHANNELS.remove(channel)
        return 'まぁ、やめよっか'
