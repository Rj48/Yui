# coding=utf-8

yui.db.execute("""\
CREATE TABLE IF NOT EXISTS quotes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel TEXT,
    quote TEXT,
    added_by TEXT,
    date_added DATETIME DEFAULT current_timestamp);""")
yui.db.commit()


@yui.command('qadd', 'qa')
def quote_add(user, channel, argv, msg):
    """Adds a quote. Usage: qadd <message>"""
    if len(argv) > 1:
        if channel == user.nick:
            channel = ''
        cursor = yui.db.execute("""\
        INSERT INTO quotes (channel, quote, added_by)
        VALUES (?, ?, ?)""", (channel, msg.split(' ', 1)[1], user.nick))
        id = cursor.lastrowid
        yui.db.commit()
        return 'Quote #%d added!' % id


@yui.command('quote', 'q')
def quote(channel, argv):
    """Displays a random quote. Usage: quote [search_string]"""
    search = None
    id = None
    if len(argv) > 1:
        search = ' '.join(argv[1:])
        if search.startswith('#'):
            try:
                id = int(search[1:])
            except ValueError:
                pass

    cursor = None
    if id:
        cursor = yui.db.execute("""\
        SELECT id, quote FROM quotes WHERE id = ?;""", (id,))
    elif search:
        cursor = yui.db.execute("""\
        SELECT id, quote FROM quotes WHERE quote LIKE ? ORDER BY RANDOM() LIMIT 1;""", ('%' + search + '%',))
    else:
        cursor = yui.db.execute("""\
        SELECT id, quote FROM quotes ORDER BY RANDOM() LIMIT 1;""")

    row = cursor.fetchone()
    if row is None:
        return "Quote #%d doesn't exist." if id else 'No results.'

    return 'Quote #%d: %s' % (row[0], yui.unhighlight_for_channel(row[1], channel))


@yui.command('qinfo')
def quote_info(argv):
    argc = len(argv)
    if argc < 2:
        cursor = yui.db.execute('SELECT COUNT(*) FROM quotes;')
        row = cursor.fetchone()
        return 'I currently have %d quotes stored.' % row[0]

    try:
        id = int(argv[1].lstrip('#'))
    except ValueError:
        return
    cursor = yui.db.execute('SELECT added_by, channel, date_added FROM quotes WHERE id = ?;', (id,))
    row = cursor.fetchone()
    if row is not None:
        chan = row[1] if row[1] != '' else 'a PM'
        return 'Quote #%d was added by %s in %s on %s' % (id, row[0], chan, row[2])
    return "Quote #%d doesn't exist." % id


@yui.admin
@yui.command('qdel')
def quote_delete(argv):
    """Delete a quote. Usage: qdelete [id]"""
    if len(argv) > 1:
        id = argv[1].lstrip('#')
        cursor = yui.db.execute('DELETE FROM quotes WHERE id = ?;', (id,))
        return 'Quote deleted!' if cursor.rowcount > 0 else "Quote #%d doesn't exist." % id
