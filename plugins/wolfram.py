# coding=utf-8

import wolframalpha

APPID = yui.config_val("wolframAppID", default=None)
CLIENT = None
if APPID is not None:
    CLIENT = wolframalpha.Client(APPID)


@yui.threaded
@yui.command('wolfram', 'wa')
def wolfram(argv):
    """Query WolframAlpha. Usage: wolfram <query>"""

    if CLIENT is None:
        return '"wolframAppID" not set in config.'
    if len(argv) < 2:
        return

    res = CLIENT.query(' '.join(argv[1:]))
    if res.success == 'false' or res.error != 'false':
        return 'Wolfram query failed :('
    return next(res.results).text.replace('\n', ' ')
