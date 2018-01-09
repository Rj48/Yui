# coding=utf-8

import json
import urllib.request

@yui.threaded
@yui.command('duckduckgo', 'ddg')
def ddg(argv):
    '''Returns the Instant Answer for a given query. Usage: ddg -lang <query>'''
    lang = 'en_US'
    if len(argv) < 1:
        return

    # check if a language was given
    argv = argv[1:]
    if len(argv) > 1 and argv[0].startswith('-'):
        lang = argv[0][1:]
        argv = argv[1:]

    q = urllib.request.quote(' '.join(argv).encode('utf-8'))
    url = f'https://api.duckduckgo.com/?q={q}&format=json&no_html=1&skip_disambig=1&no_redirect=1'
    h = { 'Accept-Language' : lang }
    req = urllib.request.Request(url, headers=h)

    with urllib.request.urlopen(req) as r:
        js = json.loads(r.read().decode('utf-8'))

    Type = js.get('Type')
    AbstractText = js.get('AbstractText')
    AbstractURL = js.get('AbstractURL')
    Heading = js.get('Heading')
    Answer = js.get('Answer')
    Redirect = js.get('Redirect')

    reply = 'No results.'

    if Type == 'D' or Type == 'C': # disambiguation or category
        reply = f'{Heading}: {AbstractURL}'
    elif Type == 'A': # article
        reply = f'{Heading}: {AbstractText} - {AbstractURL}'
    elif Type == 'E': # exclusive, e.g. calc/conversion and redirects
        if type(Answer) is str and Answer != '':
            reply = Answer
        elif type(Answer) is dict and 'result' in Answer:
            reply = Answer['result']
        elif Redirect != '':
            reply = f'Redirect: {Redirect}'

    return reply
