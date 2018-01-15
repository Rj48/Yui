# coding=utf-8

import re
import random

STATE_SIZE = 2
GENERATE_ROUNDS = 3

CHATTINESS = 0.02
ACTIVE_CHANNELS = []

yui.db.execute("""\
    CREATE TABLE IF NOT EXISTS markov_optout(
        nick TEXT COLLATE NOCASE PRIMARY KEY);""")
yui.db.commit()


class SqlMark:
    def __init__(self, db, table_name='markov', state_size=3):
        self.db = db
        self.table_name = table_name
        self.state_size = state_size
        self.separator = ' '

        db.execute("""\
            CREATE TABLE IF NOT EXISTS %s(
                tag TEXT COLLATE NOCASE,
                prefix TEXT COLLATE NOCASE,
                next_word TEXT COLLATE NOCASE,
                occurrences INTEGER,
                UNIQUE(tag, prefix, next_word));""" % self.table_name)
        db.commit()

    def delete_tag(self, tag):
        self.db.execute("DELETE FROM %s WHERE tag = ?;" % self.table_name, (tag,))
        self.db.commit()

    def add_sentence(self, tag, words):
        words = self.state_size * [''] + words + ['']
        num_words = len(words)
        for i in range(0, num_words - self.state_size, 1):
            prefix = words[i:i + self.state_size]
            next_word = words[i + self.state_size].strip()
            pref_join = self.join(prefix).strip()
            self.db.execute("""\
                INSERT OR IGNORE INTO %s(tag,prefix,next_word,occurrences)
                VALUES(?,?,?,0);""" % self.table_name, (tag, pref_join, next_word))
            self.db.execute("""\
                UPDATE %s SET occurrences = occurrences + 1
                WHERE tag = ? AND prefix = ? AND next_word = ?;""" % self.table_name, (tag, pref_join, next_word))

    def commit(self):
        self.db.commit()

    def join(self, words):
        j = self.separator.join([w for w in words if w != ''])
        return j

    def get_next_word(self, tag, prefix):
        pref_join = self.join(prefix)
        c = self.db.cursor()
        c.execute("SELECT sum(occurrences) FROM %s WHERE tag = ? AND prefix = ?;" % self.table_name, (tag, pref_join))
        max_occ = c.fetchone()[0]
        if max_occ == 0 or max_occ is None:
            return None

        rand = random.randint(0, max_occ)
        n = 0
        c.execute("SELECT next_word, occurrences FROM %s WHERE tag = ? AND prefix = ?;" % self.table_name,
                  (tag, pref_join))
        for row in c:
            n += row[1]
            if n >= rand:
                return None if row[0] == '' else row[0]
        return None

    def generate_sentence(self, tag, start=None, max_words=30):
        if start is None:
            start = ['']
        result = start
        start_len = len(start)

        while True:
            next_word = self.get_next_word(tag, result[-self.state_size:])
            if next_word is None:
                break
            next_word = next_word.strip()
            result.append(next_word)
            if len(result) >= max_words:
                break

        if len(result) > start_len:
            return ' '.join(result).strip()
        else:
            return ''


m = SqlMark(yui.db, state_size=STATE_SIZE)


def opted_out(nick):
    res = yui.db.execute("SELECT * FROM markov_optout WHERE nick = ?;", (nick,))
    return len(res.fetchall()) > 0


def generate(tag, start):
    longest = None
    for i in range(GENERATE_ROUNDS):
        gen = m.generate_sentence(tag, start)
        if longest is None or len(gen) > len(longest):
            longest = gen
    return longest


@yui.admin
@yui.command('markov_loadfile')
def load_file(argv):
    """Add a an IRC log file to the existing markov models. Messages in the file must be the same format as ZNC
    writes them, [NN:NN:NN] <NICK> MSG. Usage: markov_loadfile <path> <channel_name>"""

    if len(argv) < 3:
        return

    msg_regex = re.compile(r'^\[..:..:..\] <(.*?)> (.*)$')

    try:
        dict_file_name = argv[1]
        with open(dict_file_name, encoding='utf-8', errors='replace') as f:
            # go through all lines and extract nick + messages
            num_lines = 0
            for line in f:
                match = msg_regex.match(line)
                if not match:
                    continue
                nick = match.group(1)
                msg = match.group(2)
                spl = msg.split()
                if len(spl) < 3 or opted_out(nick):
                    continue
                m.add_sentence(nick, spl)
                m.add_sentence(argv[2], spl)
                num_lines += 1
            m.commit()
            return 'Loaded %d lines' % num_lines
    except:
        return "Couldn't read file"


def contains_mention(split):
    for w in split:
        if w.lower().strip(" ;:,.") == yui.get_nick().lower():
            return w
    return ''


# add new sentences as they come in
@yui.event('pre_recv')
def recv(channel, user, msg):
    # train the markov chains
    if channel == user.nick:  # ignore query
        return
    if opted_out(user.nick):  #ignore opted-out people
        return

    split = msg.split()
    m.add_sentence(user.nick, split)
    m.add_sentence(channel, split)
    m.commit()


    # do chatbot stuff
    if msg.startswith(tuple(yui.config_val('commandPrefixes', default=['!']))) or channel not in ACTIVE_CHANNELS:
        return

    mention = contains_mention(split)
    if mention != '' or random.random() < CHATTINESS:
        if mention != '':
            split.remove(mention)
            split.append(user.nick)
        topic = random.choice(split)
        sentence = generate(channel, [topic])
        if sentence != '':
            yui.send_msg(channel, yui.unhighlight_for_channel(sentence, channel))


@yui.command('markov', 'mark')
def markov(argv, user, channel):
    """Generate a random sentence for a given nick. Usage: markov [nick] [sentence_start]"""
    name = user.nick
    sentence_start = ['']
    if len(argv) > 1:
        name = argv[1]
    if len(argv) > 2:
        sentence_start = argv[2:2+STATE_SIZE]

    if opted_out(name):
        if name == user.nick:
            return 'You have opted out of this feature.'
        return yui.unhighlight_word(name) + ' has opted out of this feature.'

    sentence = generate(name, sentence_start)
    if sentence == '':
        return "Couldn't generate a sentence :("
    return yui.unhighlight_for_channel('<%s> %s' % (name, sentence), channel)


@yui.command('chatbot')
def chatbot(channel, argv):
    """De-/activate random chatbot for a channel. Usage: chatbot [channel]"""
    global ACTIVE_CHANNELS
    if len(argv) > 1:
        channel = argv[1]

    if channel in ACTIVE_CHANNELS:
        ACTIVE_CHANNELS.remove(channel)
        return "I'll shut up"
    ACTIVE_CHANNELS.append(channel)
    return 'Chatting now'


@yui.command('markov_optout')
def optout(user, argv):
    """Opt out of all markov functions. Your messages will no longer be incorporated into any models. Your personal markov model will be irreversibly deleted."""
    m.delete_tag(user.nick)
    yui.db.execute("INSERT OR IGNORE INTO markov_optout (nick) VALUES(?);", (user.nick,))
    yui.db.commit()
    return 'Purged your Markov model. A new one will not be built from your messages.'


@yui.command('markov_optin')
def optin(user, argv):
    """Opt back into all markov stuff. see markov_optout."""
    yui.db.execute("DELETE FROM markov_optout WHERE nick = ?;", (user.nick,))
    yui.db.commit()
    return 'Your messages will be considered for Markov models.'
