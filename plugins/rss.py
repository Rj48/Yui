# coding=utf-8
import threading

import feedparser
import time

UPDATE_INTERVAL = yui.config_val('rss', 'interval', default=30)  # update interval in minutes
LAST_UPDATE = 0
FETCHED = {}
TICKS = 0

yui.db.execute("""\
CREATE TABLE IF NOT EXISTS rss_feeds(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE);""")
yui.db.execute("""\
CREATE TABLE IF NOT EXISTS rss_seen(
    feed_id INTEGER,
    entry_id TEXT,
    UNIQUE(feed_id, entry_id) ON CONFLICT REPLACE);""")
yui.db.execute("""\
CREATE TABLE IF NOT EXISTS rss_subscriptions(
    channel TEXT COLLATE NOCASE,
    feed_id INTEGER,
    alias TEXT,
    UNIQUE(feed_id, channel) ON CONFLICT REPLACE);""")
yui.db.commit()


def fetch_thread(feeds):
    global FETCHED
    for f in feeds:
        parsed = feedparser.parse(f[1])
        if f[0] not in FETCHED:
            FETCHED[f[0]] = []
        FETCHED[f[0]].extend(parsed.entries)


@yui.event('tick')
def update():
    global TICKS
    global LAST_UPDATE
    global FETCHED

    TICKS += 1
    if TICKS > 30:
        for feed, entries in FETCHED.items():
            subs = yui.db.execute('SELECT channel, alias FROM rss_subscriptions WHERE feed_id = ?', (feed,))
            seen = yui.db.execute('SELECT entry_id FROM rss_seen WHERE feed_id=?', (feed,))
            seen = [s[0] for s in seen]
            for e in entries[:]:
                if e.id not in seen:
                    yui.db.execute('INSERT OR IGNORE INTO rss_seen(feed_id, entry_id) VALUES(?, ?)', (feed, e.id))
                    for s in subs:
                        yui.send_msg(s[0], '[%s]%s %s' % (s[1], e.title, e.link))
                entries.remove(e)
            yui.db.commit()
        TICKS = 0

    # fetch feeds every once in a while
    now = time.time()
    diff = now - LAST_UPDATE
    if diff < UPDATE_INTERVAL * 60:
        return
    LAST_UPDATE = now

    feeds = yui.db.execute('SELECT id,url FROM rss_feeds')
    feeds = [(f[0], f[1]) for f in feeds]
    threading.Thread(target=fetch_thread, args=(feeds,)).start()


@yui.command('rss')
def rss(user, channel, argv):
    """Manage RSS/Atom feeds. Usage: rss <add/list/rm>"""
    if len(argv) < 2:
        return
    verb = argv[1]
    arg = argv[2:]
    is_channel = channel != user.nick
    if verb == 'add':
        if len(arg) < 2:
            return 'Usage: rss add <alias> <url>'
        if is_channel and not yui.is_authed(user):
            return "You're not allowed to do that in a channel"

        # insert new feed
        yui.db.execute('INSERT OR IGNORE INTO rss_feeds(url) VALUES(?)', (arg[1],))
        feed_id = yui.db.execute('SELECT id FROM rss_feeds WHERE url = ?', (arg[1],))
        feed_id = feed_id.fetchone()[0]

        #insert new subscription
        yui.db.execute("""\
            INSERT OR IGNORE INTO rss_subscriptions(channel, alias, feed_id) VALUES(?, ?, ?)""", (channel, arg[0], feed_id))

        # mark all past entries as seen to prevent flooding
        parsed = feedparser.parse(arg[1])
        seen = [(feed_id, e.id) for e in parsed.entries]
        yui.db.executemany('INSERT OR IGNORE INTO rss_seen(feed_id, entry_id) VALUES(?, ?)', seen)
        yui.db.commit()
        return 'Added!'

    if verb == 'list':
        if len(arg) < 1:
            aliases = yui.db.execute('SELECT alias FROM rss_subscriptions WHERE channel = ?', (channel,))
            return ', '.join([a[0] for a in aliases])
        else:
            info = yui.db.execute('SELECT url FROM rss_subscriptions JOIN rss_feeds ON feed_id=id WHERE channel = ? and alias = ?', (channel, arg[0]))
            return info.fetchone()[0]

    if verb == 'del':
        if len(arg) < 1:
            return "Usage: rss del <alias>"
        if is_channel and not yui.is_authed(user):
            return "You're not allowed to do that in a channel"
        yui.db.execute('DELETE FROM rss_subscriptions WHERE channel = ? AND alias = ?', (channel, arg[0]))
        yui.db.execute('DELETE FROM rss_feeds WHERE id NOT IN (SELECT feed_id FROM rss_subscriptions);')
        return 'Feed removed!'
