# coding=utf-8

@yui.event('pre_send')
def up(msg):
    return msg.upper()