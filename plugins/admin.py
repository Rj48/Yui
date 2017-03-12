# coding=utf-8

import re
import sys
import os

REGEX_TIME = re.compile(r'^(?:(?P<days>\d+)[dD])?(?:(?P<hours>\d+)[hH])?(?:(?P<minutes>\d+)[mM])?$')


def time_to_seconds(time):
    match = REGEX_TIME.match(time)
    if not match:
        return None
    m = match.group('minutes')
    h = match.group('hours')
    d = match.group('days')
    minutes = int(m) if m else 0
    minutes += int(h) * 60 if h else 0
    minutes += int(d) * 60 * 24 if d else 0
    return minutes * 60


@yui.command('admin')
def admin():
    """List admins"""
    return 'Admins: %s' % ', '.join(yui.config_val('admins', default={}).keys())


@yui.command('source', 'src')
def source():
    """Link to source code"""
    return 'https://github.com/Rouji/Yui'


@yui.command('auth')
def auth(user, argv):
    """Auth yourself as an admin. Usage: auth <password>"""
    if len(argv) > 1 and yui.auth_user(user, argv[1]):
        return "You're now authorised!"


@yui.admin
@yui.command('deauth')
def deauth(argv, user):
    """Deauth a user. Usage: deauth [nick]"""
    nick = user.nick
    if len(argv) > 1:
        nick = argv[1]

    if yui.deauth_user(nick):
        return "Done."
    return "Wasn't authed."


@yui.admin
@yui.command('join')
def join(argv):
    """Join a channel. Usage: join <channel>"""
    for ch in argv[1:]:
        yui.join(ch)


@yui.admin
@yui.command('part')
def part(argv, channel):
    """Leave a channel. Usage: part <channel>"""
    if len(argv) < 2:
        yui.part(channel)
    else:
        for ch in argv[1:]:
            yui.part(ch)


@yui.admin
@yui.command('quit')
def quit_bot(argv):
    """Quit. Usage: quit [reason]"""
    if len(argv) < 2:
        yui.quit("")
    else:
        yui.quit(argv[1])


@yui.admin
@yui.command('restart')
def restart():
    """Restart the bot. Usage: restart"""
    yui.quit('')
    exe = sys.executable
    os.execl(exe, exe, *sys.argv)


@yui.admin
@yui.command('nick')
def nick(argv):
    """Change the nickname. Usage: nick <nick>"""
    if len(argv) > 1:
        yui.set_nick(argv[1])


@yui.admin
@yui.command('mode')
def mode(argv):
    """(Un)set (someone's) modes. Usage: mode [nick] <modes>"""
    if len(argv) < 2:
        return
    if len(argv) < 3:
        yui.set_mode(yui.get_nick(), argv[1])
    else:
        yui.set_mode(argv[1], argv[2])


@yui.admin
@yui.command('ignore')
def ignore(argv):
    """Ignore someone for some time. Usage: ignore <time> <nick> [user] [host]"""
    length = len(argv)
    if length < 3:
        return
    seconds = time_to_seconds(argv[1])
    if not seconds:
        return
    if yui.ignore(seconds,
                  argv[2],
                  argv[3] if length > 3 else '.*',
                  argv[4] if length > 4 else '.*'):
        return 'Done.'


@yui.admin
@yui.command('unignore')
def unignore(argv):
    """Remove an entry from the ignore list. Usage: unignore <pattern>"""
    if len(argv) < 2:
        return
    if yui.unignore(argv[1]):
        return "Done."


@yui.admin
@yui.command('ignorelist')
def ignorelist():
    """List all current ignores"""
    ign = yui.get_ignore_list()
    if ign:
        return ' '.join(ign)
    return 'None.'


@yui.admin
@yui.command('plug')
def plug(argv):
    """(Re-)loads a plugin. Usage: plug <plugin>"""
    if len(argv) < 2:
        return

    # (re)load plugin
    try:
        if yui.load_plugin(argv[1]):
            return 'Loaded %s' % argv[1]
    except Exception as ex:
        pass

    # plugin couldn't be loaded
    return 'Couldn\'t load %s' % argv[1]


@yui.admin
@yui.command('unplug')
def unplug(argv):
    """Unloads a plugin. Usage: unplug <plugin>"""
    if len(argv) < 2:
        return
    # unload plugin
    try:
        if yui.unload_plugin(argv[1]):
            return 'Unloaded %s' % argv[1]
    except Exception as ex:
        pass
    # plugin couldn't be properly unloaded
    return 'Couldn\'t unload %s' % argv[1]
