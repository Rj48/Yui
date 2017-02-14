# coding=utf-8

import sqlite3

yui.db.execute("""\
CREATE TABLE IF NOT EXISTS seen(
    nick TEXT PRIMARY KEY,
    action TEXT,
    action_date DATETIME DEFAULT current_timestamp,
    message TEXT DEFAULT '',
    message_date DATETIME DEFAULT current_timestamp);""")
yui.db.commit()


def action(nick, act):
    try:
        yui.db.execute('INSERT INTO seen(nick, action) VALUES(?,?)', (nick, act))
    except sqlite3.IntegrityError:
        yui.db.execute('UPDATE seen SET action = ? WHERE nick = ?', (act, nick))
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


    in_chans = []
    for chan in yui.joined_channels():
        if nick.lower() in [x.lower() for x in yui.nicks_in_channel(chan)]:
           in_chans.append(chan)
    if len(in_chans) > 0:
        if channel in in_chans:
            return argv[1] + ' is currently here!'
        return '%s is currently in channel(s): %s' % (nick, ', '.join(in_chans))

    cursor = yui.db.execute("SELECT nick, action, datetime(action_date, 'localtime') FROM seen WHERE nick = ? COLLATE NOCASE", (argv[1],))
    rows = cursor.fetchall()
    if len(rows) < 1:
        return 'Who?'
    row = rows[0]
    return '%s was last seen %s on %s' % (row[0], row[1], row[2])
