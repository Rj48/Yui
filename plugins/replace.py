import re

LAST = {}
REGEX = re.compile('s/(.*?)/(.*)')


@yui.event('msgRecv')
def replace(msg, channel, user):
    global LAST

    match = REGEX.match(msg)
    key = channel + user.nick
    if not match:
        if key not in LAST.keys():
            LAST[key] = msg
        return

    last_msg = LAST[key]
    search = match.group(1)
    repl = match.group(2)
    if repl.endswith('/g'):
        last_msg = last_msg.replace(search, repl[:-2])
    else:
        if repl.endswith('/'):
            repl = repl[:-1]
        last_msg = last_msg.replace(search, repl, 1)

    yui.send_msg(channel, yui.unhighlight_for_channel('<%s> %s' % (user.nick, last_msg), channel))
