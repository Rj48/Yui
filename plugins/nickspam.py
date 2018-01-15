# coding=utf-8

import re
from collections import deque

MAX_HIGHLIGHTS = yui.config_val('nickspam', 'maxHighlights', default=10)
MSG_COUNT = yui.config_val('nickspam', 'msgCount', default=4)
HIGHLIGHTS = {}


@yui.event('pre_recv')
def nickspam(msg, user, channel):
    # ignore query/pm
    if channel == user.nick:
        return

    chan_nicks = yui.nicks_in_channel(channel)
    num_highlight = sum([1 if nick in re.split('[.,;:!?\'" ]+', msg) else 0 for nick in chan_nicks])

    key = channel + ' ' + user.nick
    if key not in HIGHLIGHTS.keys():
        HIGHLIGHTS[key] = deque(maxlen=MSG_COUNT)
    HIGHLIGHTS[key].append(num_highlight)

    if sum(HIGHLIGHTS[key]) > MAX_HIGHLIGHTS:
        yui.kick(channel, user.nick, 'spam')
        return '%s spammed %d nicks in their last %d messages' % (user.nick, sum(HIGHLIGHTS[key]), len(HIGHLIGHTS.pop(key)))
