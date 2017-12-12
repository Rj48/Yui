from langdetect import detect, DetectorFactory, lang_detect_exception

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


@yui.event('msgRecv')
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
        yui.kick(channel, user.nick, '(´・ω・｀)')

    if LANGCOUNTS[key] < 2:
        return '%s: %sでおk' % (user.nick, ACTIVE_CHANNELS[channel])


@yui.admin
@yui.command('langordie')
def switch(channel, argv):
    """Keep people talking in ONE language. Usage: langordie <2 char lang code>"""
    if len(argv) < 2:
        return
    if channel in ACTIVE_CHANNELS:
        ACTIVE_CHANNELS.pop(channel)
        return 'まぁ、やめよっか'
    ACTIVE_CHANNELS[channel] = argv[1]
    return '頑張ってね o/'


@yui.command('langstats', 'ls')
def langstats(channel, user, argv):
    """Language stats for someone in this channel. Usage: langstats [nick]"""
    n = user.nick
    if len(argv) > 1:
        n = argv[1]
    res = yui.db.execute('SELECT lang, cnt FROM langstats WHERE channel = ? AND nick = ? ORDER BY cnt DESC;',
                         (channel, n))
    return yui.unhighlight_word(n) + ': ' + ', '.join(['%d %s' % (r[1], r[0]) for r in res.fetchall()])
