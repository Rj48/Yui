import re

LAST = {}
REGEX = re.compile('s/(.*?)/(.*)')


@yui.event('msgRecv')
def replace(msg, channel, user):
    global LAST

    match = REGEX.match(msg)
    key = channel + user.nick
    if not match:
        LAST[key] = msg
        return

    if key not in LAST.keys():
        return

    last_msg = LAST[key]
    new_msg = last_msg
    search = match.group(1)
    repl = match.group(2)
    if repl.endswith('/g'):
        new_msg = last_msg.replace(search, repl[:-2])
    else:
        if repl.endswith('/'):
            repl = repl[:-1]
        new_msg = last_msg.replace(search, repl, 1)

    if new_msg != last_msg:
        yui.send_msg(channel, yui.unhighlight_for_channel('<%s> %s' % (user.nick, new_msg), channel))
