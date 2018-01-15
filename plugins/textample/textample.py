# coding=utf-8

import gzip
import os
import random
import re


def search(regex, base_dir, file_contains=''):
    reg = re.compile(regex, re.IGNORECASE)
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.gz'):
                file_path = os.path.join(root, file)
                if file_contains not in file_path:
                    continue
                with gzip.open(file_path) as f:
                    for line in f:
                        line = line.decode('utf-8')
                        if reg.search(line):
                            line = ' '.join(line.split())
                            yield (file_path[len(base_dir) + 1:-len('.gz')], line)


def underline(regex, line):
    return re.sub(regex, lambda m: '\x1F' + m[0] + '\x1F', line, flags=re.IGNORECASE)


@yui.threaded
@yui.command('example', 'ex')
def example(argv):
    """Regex search for sentences. Usage: example <regex> [file]"""
    if len(argv) < 2:
        return

    base = os.path.join(os.path.dirname(__file__), 'texts')
    if not os.path.isdir(base):
        return 'Directory %s does not exist' % base

    se = search(argv[1], base, file_contains=argv[2] if len(argv) > 2 else '')
    try:
        ret = []
        l = list(se)
        for _ in range(0,20):
            file, line = random.choice(l)
            ret.append('%s: %s' % (file, underline(argv[1], line)))
        return '\n'.join(ret)
    except IndexError as e:
        return 'No matching sentences found'
