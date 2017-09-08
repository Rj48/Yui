# coding=utf-8

import errno
import re
import socket
import ssl
import time
from collections import namedtuple

Prefix = namedtuple('Prefix', ['nick', 'user', 'host', 'raw'])
ServerCmd = namedtuple('ServerCmd', ['prefix', 'cmd', 'args'])


class IRCClient(object):
    def __init__(self,
                 server='127.0.0.1',
                 port=6667,
                 ssl=True,
                 encoding='utf-8',
                 nick='yetanotherbot',
                 user=None,
                 password=None,
                 realname='',
                 timeout=120):
        self.socket = None
        self.quitting = False

        self.server = server
        self.port = port
        self.ssl = ssl
        self.encoding = encoding
        self.nick = nick
        self.user = user
        self.password = password
        self.realname = realname
        self.timeout = timeout

        self.channel_nicks = {}  # channel name -> set of nicks

        self.max_msg_len = 400

        self.bad_chars_regex = re.compile(r'[\r\n]+')

    def send_raw(self, msg):
        """Send a raw line to the server"""
        try:
            # strip newlines
            stripped = self.bad_chars_regex.sub(' ', msg)

            # clamp length
            if len(stripped) > self.max_msg_len:
                stripped = stripped[:self.max_msg_len]

            stripped += '\r\n'
            encoded = stripped.encode(self.encoding)

            self.socket.send(encoded)

        except TypeError as ex:
            return False  # invalid msg
        except Exception as ex:
            # something else went horribly wrong, disconnect

            self.on_log('Exception while sending data: %s' % repr(ex))
            self.disconnect()
        return True

    # TODO: this seems a bit inefficient
    def trim_to_max_len(self, string, trail=''):
        """Trim a string to the max. message (byte) length, replace
        last few characters with a given trail (e.g. '...')"""
        if not string:
            return None
        enc_str = string.encode(self.encoding)
        if len(enc_str) < self.max_msg_len:
            return string
        enc_trail = trail.encode(self.encoding)
        enc_str = enc_str[:self.max_msg_len - len(enc_trail)]
        dec = enc_str.decode(self.encoding, 'ignore')
        dec += trail
        return dec

    def joined_channels(self):
        return self.channel_nicks.keys()

    def nicks_in_channel(self, channel):
        if channel not in self.channel_nicks:
            return set()
        return self.channel_nicks[channel]

    def send_privmsg(self, channel, msg):
        """Send a message to a channel/user"""
        if not channel or not msg:
            return
        self.send_raw('PRIVMSG %s :%s' % (channel, msg))

    def set_nick(self, nick):
        """Set the bot's nick"""
        self.send_raw('NICK %s' % nick)

    def set_mode(self, nick, mode):
        self.send_raw('MODE %s %s' % (nick, mode))

    def join(self, channel):
        """Join a channel"""
        self.send_raw('JOIN %s' % channel)
        if channel not in self.channel_nicks.keys():
            self.channel_nicks[channel] = set()

    def part(self, channel):
        """Leave a channel"""
        self.send_raw('PART %s' % channel)
        self.channel_nicks.pop(channel, None)

    def quit(self, reason):
        """Quit from the server and end the main loop gracefully"""
        self.send_raw('QUIT :%s' % reason)
        self.quitting = True

    def kick(self, channel, nick, reason = None):
        """Kick someone from a channel"""
        if reason is None:
            self.send_raw('KICK %s %s' % (channel, nick))
        else:
            self.send_raw('KICK %s %s %s' % (channel, nick, reason))

    def parse_server_cmd(self, cmd):
        """Parse a message received from the server and split it into manageable parts.
        *inspired by* twisted's irc implementation"""
        prefix = ''
        trailing = []
        if not cmd:
            return None
        try:
            if cmd[0] == ':':
                prefix, cmd = cmd[1:].split(' ', 1)
            if cmd.find(' :') != -1:
                cmd, trailing = cmd.split(' :', 1)
                args = cmd.split()
                args.append(trailing)
            else:
                args = cmd.split()
            cmd = args.pop(0)
            return ServerCmd(prefix, cmd, args)
        except Exception as ex:
            self.on_log('Received invalid message from server: %s' % cmd)
            return None

    def handle_server_cmd(self, cmd):
        """Handle a received command (that has been parsed by parseServerCmd())"""
        handler = getattr(self, 'cmd_%s' % cmd.cmd, None)
        if handler:
            handler(self.split_prefix(cmd.prefix), cmd.args)

    def split_prefix(self, prefix):
        """Extract the nick, user and host from a prefix"""
        split = prefix.split('!')
        nick = split[0]
        user = None
        host = None
        if len(split) > 1:
            split = split[1].split('@')
            user = split[0]
            if len(split) > 1:
                host = split[1]
        return Prefix(nick, user, host, prefix)

    def cmd_NICK(self, prefix, args):
        new_nick = args[0]

        # update own nick
        if prefix.nick == self.nick:
            self.nick = new_nick

        # update other people's nicks
        for chan, nicks in self.channel_nicks.items():
            try:
                nicks.discard(prefix.nick)
                nicks.add(new_nick)
            except KeyError:
                pass

        self.on_nick(prefix, args[0])

    def cmd_PING(self, prefix, args):
        self.send_raw('PONG :%s' % args[0])

    def cmd_PRIVMSG(self, prefix, args):
        self.on_privmsg(prefix, args[0], args[1])

    def cmd_NOTICE(self, prefix, args):
        self.on_notice(prefix, args[0], args[1])

    def cmd_QUIT(self, prefix, args):
        for chan, nicks in self.channel_nicks.items():
            nicks.discard(prefix.nick)
        self.on_quit(prefix)

    def cmd_ERROR(self, prefix, args):
        self.on_error(args[0])
        self.disconnect()

    def cmd_JOIN(self, prefix, args):
        channel = args[0]

        # add newly joined nick
        if channel in self.channel_nicks.keys():
            self.channel_nicks[channel].add(prefix.nick)

        # send a WHO, if we joined somewhere
        if prefix.nick == self.nick:
            self.send_raw('WHO ' + channel)

        self.on_join(prefix, channel)

    def cmd_PART(self, prefix, args):
        chan = args[0]
        if chan in self.channel_nicks.keys():
            self.channel_nicks[chan].discard(prefix.nick)
        self.on_part(prefix, chan)

    # ErrNickNameInUse
    def cmd_433(self, prefix, args):
        self.nick = args[1] + '_'
        self.set_nick(self.nick)

    # ErrNoMotd
    def cmd_422(self, prefix, args):
        self.on_serverready()

    # EndOfMotd
    def cmd_376(self, prefix, args):
        self.on_serverready()

    # whoreply
    def cmd_352(self, prefix, args):
        try:
            chan = args[1]
            nick = args[5]
            if chan in self.channel_nicks.keys():
                self.channel_nicks[chan].add(nick)
        except:
            pass

    def on_nick(self, prefix, new):
        pass

    def on_join(self, prefix, channel):
        pass

    def on_part(self, prefix, channel):
        pass

    def on_quit(self, prefix):
        pass

    def on_connect(self):
        pass

    def on_disconnect(self):
        pass

    def on_serverready(self):
        pass

    def on_privmsg(self, prefix, target, msg):
        pass

    def on_notice(self, prefix, target, msg):
        pass

    def on_rawmsg(self, msg):
        """raw data from the server"""
        pass

    def on_error(self, error):
        pass

    def on_tick(self):
        """Called once roughly every second"""
        pass

    def on_log(self, msg):
        pass

    def connect(self):
        """Try to connect to the server"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # enable ssl
        if self.ssl:
            self.socket = ssl.wrap_socket(self.socket)
        try:
            self.socket.connect((self.server, self.port))
            self.socket.setblocking(False)

            if self.password:
                self.send_raw('PASS %s' % self.password)

            self.set_nick(self.nick)
            if self.user:
                self.send_raw('USER %s 0 * :%s' % (self.user, self.realname))
        except Exception as ex:
            self.on_log('Connecting failed: %s' % repr(ex))
            return False

        self.on_connect()
        return True

    def disconnect(self):
        """Disconnect from the server, but don't quit the main loop."""
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
                self.on_disconnect()
                return True
            except:
                pass
        return False

    def run(self):
        """Main loop"""
        while not self.quitting:
            # try connecting indefinitely
            while not self.connect():
                time.sleep(30)

            # main recv loop
            recv = ''
            last_time = time.time()  # timestamp for detecting timeouts
            last_tick = time.time()
            sent_ping = False
            while not self.quitting:
                try:
                    now = time.time()
                    diff = now - last_time

                    # call on_tick every second
                    if now - last_tick > 1.0:
                        self.on_tick()
                        last_tick = time.time()

                    # send a ping at half the timeout
                    if diff > self.timeout / 2.0 and not sent_ping:
                        self.send_raw('PING :%s' % self.nick)
                        sent_ping = True

                    # no messages received after timeout, try to reconnect
                    if diff > self.timeout:
                        break

                    recv += self.socket.recv(4098).decode(self.encoding, 'ignore')

                    last_time = now
                    sent_ping = False
                except socket.error as e:
                    err = e.args[0]
                    # sleep for a short time, if no data was received
                    if err == errno.EAGAIN or err == errno.EWOULDBLOCK or err == errno.ENOENT:
                        time.sleep(0.1)
                        continue
                except Exception as ex:
                    self.on_log('Exception occurred receiving data: %s' % repr(ex))
                    break  # break inner loop, try to reconnect

                # split received data into messages and process them
                while '\r\n' in recv:
                    line, recv = recv.split('\r\n', 1)
                    self.on_rawmsg(line)
                    cmd = self.parse_server_cmd(line)
                    if cmd:
                        self.handle_server_cmd(cmd)

            self.disconnect()

        return True
