# coding=utf-8

import subprocess

@yui.admin
@yui.threaded
@yui.command('git_pull')
def git_pull(argv):
    """Does a git pull on the working dir of the bot. Usage: git_pull [repo]"""

    args = ['git', 'pull']
    if len(argv) > 1:
        args.append(argv[1])

    proc = subprocess.Popen(args)
    code = proc.wait()
    if code == 0:
        return "git pull's done!"
    else:
        return "git pull failed :("


