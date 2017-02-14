# coding=utf-8

import re

import dateutil.parser

yui.db.execute("""\
CREATE TABLE IF NOT EXISTS remind(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nick TEXT,
    channel TEXT,
    msg TEXT,
    date_remind DATETIME,
    date_added DATETIME DEFAULT current_timestamp);""")

yui.db.execute("""\
CREATE TABLE IF NOT EXISTS tell(
    nick TEXT,
    channel TEXT,
    msg TEXT,
    added_by TEXT,
    date_added DATETIME DEFAULT current_timestamp);""")
yui.db.commit()

REGEX_TIME = re.compile(r'^(?:(?P<days>\d+)[dD])?(?:(?P<hours>\d+)[hH])?(?:(?P<minutes>\d+)[mM])?$')


def time_to_minutes(time):
    match = REGEX_TIME.match(time)
    if not match:
        return None
    m = match.group('minutes')
    h = match.group('hours')
    d = match.group('days')
    min = int(m) if m else 0
    min += int(h) * 60 if h else 0
    min += int(d) * 60 * 24 if d else 0
    return min


@yui.command('remind', 'rem')
def remind(user, channel, argv):
    """Remind yourself of something. Usage: remind <time> [message]"""
    if len(argv) < 2:
        return

    min = time_to_minutes(argv[1])
    msg = ''
    if len(argv) > 2:
        msg = ' '.join(argv[2:])

    try:
        if min:
            yui.db.execute("""\
                INSERT INTO remind(nick, channel, msg, date_remind)
                VALUES(?,?,?,DATETIME(current_timestamp, ?))""", (user.nick, channel, msg, '+%s minutes' % min))
        else:
            datetime = dateutil.parser.parse(argv[1])
            if datetime < datetime.now():
                return "That time's already passed"
            yui.db.execute("""\
                INSERT INTO remind(nick, channel, msg, date_remind)
                VALUES(?,?,?,DATETIME(?))""", (user.nick, channel, msg, datetime.strftime('%Y-%m-%d %H:%M')))
        yui.db.commit()
    except Exception as ex:
        return

    return "I'll remind you"


@yui.event('tick')
def tick():
    cursor = yui.db.execute("""\
        SELECT id, nick, channel, msg, time(datetime(date_added, 'localtime')) FROM remind
        WHERE date_remind < current_timestamp ORDER BY date_added LIMIT 1""")
    rows = cursor.fetchall()
    if len(rows) < 1:
        return
    row = rows[0]
    if len(row[3]) < 1:
        yui.send_msg(row[2], 'Reminder for %s [%s]' % (row[1], row[4]))
    else:
        yui.send_msg(row[2], 'Reminder for %s: %s [%s]' % (row[1], row[3], row[4]))

    cursor = yui.db.execute("""\
        DELETE FROM remind WHERE id = ?""", (row[0],))
    yui.db.commit()


@yui.command('tell')
def tell(user, channel, argv, msg):
    """Tell someone something next time they join. Usage: tell <nick> <message>"""
    if len(argv) < 3:
        return
    msg = msg.split(' ', 2)[2]
    yui.db.execute("""\
        INSERT INTO tell(nick, channel, msg, added_by)
        VALUES(?,?,?,?)""", (argv[1], channel, msg, user.nick))
    yui.db.commit()
    return "I'll tell them"

@yui.command('tellme')
def tellme(user, channel):
    """Tells you stuff people told me to tell you."""
    say_tell(user, channel)

@yui.event('join')
def join(user, channel):
    say_tell(user, channel)

def say_tell(user, channel):
    cursor = yui.db.execute("""\
        SELECT nick,channel,msg,added_by FROM tell
        WHERE nick=? AND channel=?""", (user.nick, channel))
    rows = cursor.fetchall()
    if len(rows) < 1:
        return
    cursor = yui.db.execute("""\
        DELETE FROM tell WHERE nick=? AND channel=?""", (user.nick, channel))
    yui.db.commit()
    tells = ['<%s> %s' % (r[3], r[2]) for r in rows]
    yui.send_msg(channel, 'Hi %s, I was told to tell you: %s' % (user.nick, ' | '.join(tells)))
