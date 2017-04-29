# coding=utf-8

import subprocess

@yui.admin
@yui.threaded
@yui.command('git')
def git(argv):
    """Basic git commands"""

    if len(argv) < 2:
        return

    verb = argv[1]
    arg = argv[2:]
    if verb == 'pull':
        args = ['git', 'pull']
        if len(arg) > 1:
            args.append(argv[1])

        proc = subprocess.Popen(args)
        code = proc.wait()
        if code == 0:
            return "Pulled all the gits!"
        else:
            return "Couldn't pull the gits :("


