# coding=utf-8

import random
import re

builtin_phrases = [
    ['hi', 'hello'],
    ['yo', 'sup'],
    ['hallo', 'tag', 'moin'],
    ['こんにちは', 'こんちわ'],
    ['よ', 'やぁ', 'おっす']
]

phrases = yui.config_val("greetings", default=builtin_phrases)

def getRandomExcept(arr, ex):
    if not ex in arr:
        return random.choice(arr)
    idx = arr.index(ex)
    arrEx = arr[:idx] + arr[idx + 1:]
    return random.choice(arrEx)


@yui.event('msgRecv')
def greetings(msg, channel):
    global phrases

    answer = None
    lower = msg.lower()
    lower = re.sub('[!?\. ]', '', lower)
    for s in phrases:
        if lower in s:
            yui.send_msg(channel, getRandomExcept(s, lower))
