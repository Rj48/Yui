# coding=utf-8

import sqlite3

yui.db.execute("""\
CREATE TABLE IF NOT EXISTS seen(
    nick TEXT PRIMARY KEY COLLATE NOCASE,
    action TEXT,
    action_date DATETIME DEFAULT current_timestamp,
    message TEXT DEFAULT '',
    message_date DATETIME DEFAULT current_timestamp,
    message_channel TEXT DEFAULT '');""")
yui.db.commit()


def action(nick, act):
    yui.db.execute('INSERT OR IGNORE INTO seen(nick) VALUES(?)', (nick,))
    yui.db.execute('UPDATE seen SET action = ?, action_date = current_timestamp WHERE nick = ?', (act, nick))
    yui.db.commit()


@yui.event('pre_recv')
def recv(user, msg, channel):
    if not channel.startswith("#"):
        return

    msg = '<%s> %s' % (user.nick, msg)

    yui.db.execute('INSERT OR IGNORE INTO seen(nick) VALUES(?)', (user.nick,))
    yui.db.execute('UPDATE seen SET message = ?, message_channel = ?, message_date = current_timestamp WHERE nick = ?', (msg, channel, user.nick))
    yui.db.commit()


@yui.event('join')
def join(user, channel):
    action(user.nick, 'joining channel ' + channel)


@yui.event('part')
def part(user, channel):
    action(user.nick, 'leaving channel ' + channel)


@yui.event('quit')
def quit(user):
    action(user.nick, 'quitting')


@yui.command('seen')
def seen(argv, channel):
    """When a given nick was last seen. Usage: seen <nick>"""
    if len(argv) < 2:
        return

    nick = argv[1]

    action_part = ''
    msg_part = ''

    cursor = yui.db.execute("""
        SELECT nick, action, datetime(action_date, 'localtime'),
            message, message_channel, datetime(message_date, 'localtime')
        FROM seen WHERE nick = ?""", (argv[1],))
    rows = cursor.fetchall()
    if len(rows) > 0:
        row = rows[0]
        if row[1]:
            action_part = '%s was last seen %s on %s.' % (argv[1], row[1], row[2])
        if row[3]:
            msg_part = 'Last msg %s in %s: %s' % (row[5], row[4], row[3])

    in_chans = []
    for chan in yui.joined_channels():
        if nick.lower() in [x.lower() for x in yui.nicks_in_channel(chan)]:
           in_chans.append(chan)
    if len(in_chans) > 0:
        if channel in in_chans:
            action_part =  argv[1] + ' is currently here!'
        else:
            action_part = '%s is currently in channel(s) %s.' % (nick, ', '.join(in_chans))

    if action_part:
        return action_part + (' ' + msg_part if msg_part else '')

    if msg_part:
        return "%s's %s" % (argv[1], msg_part)

    return "Who?"

