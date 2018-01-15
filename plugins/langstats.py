# coding=utf-8

from langdetect import detect, detect_langs, DetectorFactory, lang_detect_exception

yui.db.execute("""\
CREATE TABLE IF NOT EXISTS langstats(
    channel TEXT COLLATE NOCASE,
    nick TEXT COLLATE NOCASE,
    lang TEXT,
    cnt INTEGER,
    UNIQUE(channel, nick, lang));""")
yui.db.commit()

DetectorFactory.seed = 0
ACTIVE_CHANNELS = {}
LANGCOUNTS = {}
CHANCES = 10


def clamp(n, min_val, max_val):
    return max(min_val, min(n, max_val))


@yui.event('pre_recv')
def recv(channel, user, msg, is_cmd):
    if is_cmd:
        return

    try:
        lang = detect(msg)
    except lang_detect_exception.LangDetectException as e:
        return

    yui.db.execute('INSERT OR IGNORE INTO langstats(channel, nick, lang, cnt) VALUES(?, ?, ?, 0);',
                   (channel, user.nick, lang))
    yui.db.execute('UPDATE langstats SET cnt = cnt + 1 WHERE channel = ? AND nick = ? AND lang = ?;',
                   (channel, user.nick, lang))
    yui.db.commit()

    if channel not in ACTIVE_CHANNELS:
        return

    key = channel + user.nick
    if key not in LANGCOUNTS:
        LANGCOUNTS[key] = CHANCES

    LANGCOUNTS[key] = clamp(LANGCOUNTS[key] + (1 if lang == ACTIVE_CHANNELS[channel] else -1),
                            0,
                            CHANCES)

    if LANGCOUNTS[key] < 1:
        LANGCOUNTS.pop(key)
        yui.kick(channel, user.nick, '(´・ω・｀)')
        return

    if LANGCOUNTS[key] < 2:
        return '%s: %sでおk' % (user.nick, ACTIVE_CHANNELS[channel])


@yui.admin
@yui.command('langordie')
def switch(channel, argv):
    """Keep people talking in ONE language. Usage: langordie [lang_code [channel]]"""
    if len(argv) < 2:
        return
    c = channel if len(argv) < 3 else argv[2]
    if c in ACTIVE_CHANNELS:
        ACTIVE_CHANNELS.pop(c)
        return 'まぁ、やめよっか'
    if len(argv) > 1:
        ACTIVE_CHANNELS[c] = argv[1]
        return '頑張ってね o/'


@yui.command('langstats', 'ls')
def langstats(channel, user, argv):
    """Language stats for someone in this channel. Usage: langstats [nick]"""
    n = user.nick
    if len(argv) > 1:
        n = argv[1]
    res = yui.db.execute('SELECT lang, cnt FROM langstats WHERE channel = ? AND nick = ? ORDER BY cnt DESC;',
                         (channel, n))
    rows = res.fetchall()
    if len(rows) > 0:
        return yui.unhighlight_word(n) + ': ' + ', '.join(['%d %s' % (r[1], r[0]) for r in rows])


@yui.command('langdetect', 'ld')
def langdet(argv):
    """Try to detect what language a string likely is. Usage: langdetect <string>"""
    try:
        lang = detect_langs(' '.join(argv[1:]))
    except lang_detect_exception.LangDetectException as e:
        return 'No idea what language that is.'

    return ', '.join(['%s:%.2f' % (n.lang, n.prob) for n in lang])
