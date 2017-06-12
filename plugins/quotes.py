# coding=utf-8

import random

yui.db.execute("""\
CREATE TABLE IF NOT EXISTS quotes(
    tag TEXT,
    quote TEXT,
    added_by TEXT,
    date_added DATETIME DEFAULT current_timestamp);""")
yui.db.commit()


@yui.command('qadd', 'qa')
def quoteAdd(user, channel, argv, msg):
    """Adds a quote. Usage: qadd [-tag] <message>"""
    tag = channel
    if len(argv) > 1 and argv[1].startswith('-'):
        tag = argv[1][1:]
        argv = argv[1:]
        if not tag:
            return
        msg = msg.split(' ', 1)[1]

    if len(argv) > 1:
        yui.db.execute("""\
        INSERT INTO quotes (tag, quote, added_by)
        VALUES (?, ?, ?)""", (tag, msg.split(' ', 1)[1], user.nick))
        yui.db.commit()
        return 'Added quote to [%s]!' % tag


@yui.command('quote', 'q')
def quote(channel, argv):
    """Displays a random quote. Usage: quote [-tag] [search_string]"""
    tag = channel
    search = None
    if len(argv) > 1 and argv[1].startswith('-'):
        tag = argv[1][1:]
        argv = argv[1:]
        if not tag:
            return

    if len(argv) > 1:
        search = ' '.join(argv[1:])

    cursor = None
    if search:
        cursor = yui.db.execute("""\
        SELECT quote FROM quotes WHERE tag = ? AND quote LIKE ?""", (tag, '%' + search + '%'))
    else:
        cursor = yui.db.execute("""\
        SELECT quote FROM quotes WHERE tag = ?""", (tag,))

    rows = cursor.fetchall()
    cnt = len(rows)
    if cnt < 1:
        return 'I got nothing'
    rnd = random.randint(0, cnt - 1)
    row = rows[rnd]

    return 'Quote for [%s] (%d/%d): %s' % (tag, rnd + 1, cnt, yui.unhighlight_for_channel(row[0], channel))


@yui.command('qtags', 'qt')
def quoteTags():
    """Lists all quote tags."""
    cursor = yui.db.execute("""\
    SELECT tag, count(*) FROM quotes GROUP BY tag""")
    tags = cursor.fetchall()
    tags = ['%s (%d)' % (t[0], t[1]) for t in tags]

    return 'Tags: ' + ', '.join(tags)
