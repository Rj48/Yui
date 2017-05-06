# coding=utf-8

from google import search

@yui.threaded
@yui.command('google', 'g')
def g(argv):
    """Returns the first few google results for a search. Usage: google [-lang] <search>"""
    lang = 'en'
    if len(argv) < 2:
        return

    # check if a language was given
    argv = argv[1:]
    if len(argv) > 1 and argv[0].startswith('-'):
        lang = argv[0][1:]
        argv = argv[1:]

    term = ' '.join(argv)
    urls = [res for res in search(term, lang=lang, stop=5)]
    if len(urls) < 1:
        return "No search results for '%s'." % term
    return term + ': ' + ' | '.join(urls[:3])
