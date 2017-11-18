# coding=utf-8

import inspect


@yui.command('help', 'h')
def help(argv):
    """Returns doc for commands. For a list of commands available, use the "commands" command. Usage: help <command>"""
    if len(argv) < 2:
        return help.__doc__
    hook = yui.find_hook(lambda h: argv[1] in h.cmd)
    if hook:
        doc = inspect.getdoc(hook.func)
        if doc:
            return doc
    return "Couldn't find command \"%s\"" % argv[1]


@yui.command('alias', 'al')
def alias(argv):
    """Returns all aliases for a command. Usage: alias <command>"""
    if len(argv) < 2:
        return
    hook = yui.find_hook(lambda h: argv[1] in h.cmd)
    if hook:
        return 'Aliases for %s: %s' % (argv[1], ', '.join(hook.cmd))


@yui.command('commands', 'cmds')
def commands(argv, user):
    """Lists one alias for every registered command. Usage: commands [search]"""
    cmds = []
    search = None
    if len(argv) > 1:
        search = argv[1]
    for h in yui.get_all_hooks():
        if h.admin and not yui.is_authed(user):
            continue
        if h.cmd:
            if not search:
                cmds.append(h.cmd[0])
            else:
                for c in h.cmd:
                    if search in c:
                        cmds.append(c)
                        break
    if cmds:
        return 'commands: ' + ', '.join(cmds)
