# coding=utf-8

import wikipedia


@yui.threaded
@yui.command('wiki', 'wk', 'w')
def wiki(argv):
    """Prints summary of Wikipedia atricles. Usage: wiki [-lang] <article>"""
    lang = 'en'
    if len(argv) < 2:
        return

    # check if a language was given
    argv = argv[1:]
    if len(argv) > 1 and argv[0].startswith('-'):
        lang = argv[0][1:]
        argv = argv[1:]

    article = ' '.join(argv)
    try:
        wikipedia.set_lang(lang)
        summary = ' '.join(wikipedia.summary(article).split())
    except Exception as ex:
        return "Couldn't find an article for '%s'" % article
    return summary
