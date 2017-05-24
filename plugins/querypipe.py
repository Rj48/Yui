@yui.event('msgRecv')
def query(channel, user, msg):
    if channel != user.nick:
        return
    m = '<' + user.nick + '> ' + msg
    for authed in yui.authed_users:
        yui.send_msg(authed.nick, m)
