# coding=utf-8

import re
from collections import deque

MAX_NICKS = yui.config_val('nickspam', 'maxNicks', default=10)
MSG_COUNT = yui.config_val('nickspam', 'msgCount', default=4)
USERS = {}


@yui.event('msgRecv')
def antispam(msg, user, channel):
    # ignore query/pm
    if channel == user.nick:
        return

    nicks_in_chan = yui.nicks_in_channel(channel)
    num_highlight = sum([1 if nick in re.split('[.,;:!?\'" ]+', msg) else 0 for nick in nicks_in_chan])

    key = channel + ' ' + user.nick
    if key not in USERS.keys():
        USERS[key] = deque(maxlen=MSG_COUNT)
    USERS[key].append(num_highlight)

    if sum(USERS[key]) > MAX_NICKS:
        yui.kick(channel, user.nick, 'spam')
        return '%s spammed %d nicks in their last %d messages' % (user.nick, sum(USERS[key]), len(USERS.pop(key)))
