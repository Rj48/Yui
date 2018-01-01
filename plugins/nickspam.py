# coding=utf-8

import re
from collections import deque

MAX_NICKS = yui.config_val('nickspam', 'maxNicks', default=10)
MSG_COUNT = yui.config_val('nickspam', 'msgCount', default=4)
USERS = {}


@yui.event('msgRecv')
def antispam(msg, user, channel):
    if channel == user.nick:
        return
    nicks = yui.nicks_in_channel(channel)
    n = sum([1 if nick in re.split('[.,;:!?\'" ]+', msg) else 0 for nick in nicks])
    key = channel + ' ' + user.nick
    if key not in USERS.keys():
        USERS[key] = deque(maxlen=MSG_COUNT)
    USERS[key].append(n)
    if sum(USERS[key]) > MAX_NICKS:
        yui.kick(channel, user.nick)
        return '%s spammed %d nicks in his last %d messages' % (user.nick, sum(USERS[key]), len(USERS[key]))
