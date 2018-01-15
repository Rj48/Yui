# coding=utf-8

@yui.event('pre_recv')
@yui.event('noticeRecv')
def query(channel, user, msg):
    if channel != user.nick:
        return
    m = '<' + user.nick + '> ' + msg
    for authed in yui.authed_users:
        if user.nick != authed.nick:
            yui.send_msg(authed.nick, m)
