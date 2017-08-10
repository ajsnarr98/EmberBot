import asyncio

import discord
from discord.ext import commands

from .core import AutoResponse, auto_response

class Convenience(object):
    """ Convenience functions for the bot. """
    def __init__(self, bot):
        self.bot = bot

    @auto_response()
    @asyncio.coroutine
    def help_incorrect(self, bot, message):
        """ For when someone types 'help' without the command prefix. """
        if message.content.lower() == 'help':
            response = 'Did you mean \"{0}help\" ?'
            
            prefix = bot.default_command_prefix

            yield from bot.send_message(
                message.channel,
                response.format(prefix))

    @auto_response()
    @asyncio.coroutine
    def multi_account_mention(self, bot, message):
        """ A convenience function for users who have two accounts.
            If a user is @mentioned, and has two or more accounts,
            all his/her accounts will be @mentioned.
        """
        accounts_filename = 'linked_accounts.json'

        mention_str = '<@{id}>'
        output = ''

        accounts_info = bot.data_man.load_json(accounts_filename)

        if accounts_info:
            for member in message.mentions:
                if accounts_info.get(member.id, None): # if member id in dict
                    for account_id in accounts_info.get(member.id, None):
                        output += mention_str.format(id=account_id) + ' '

            if output != '':
                yield from bot.send_message(
                    message.channel,
                    output)
        else:
            accounts_info = {'description' :
                                'Use this file to link accounts.' +
                                ' Aka, say that two accounts belong' +
                                ' to the same person. Usefull for' +
                                ' the multi_account_mention auto-response,' +
                                ' which you can see by looking at' +
                                ' auto_responses through settings.',
                             'example' : {
                                    '<member id 1>' : [
                                        '<member id 1>',
                                        '<member id 2>'
                                    ],
                                    '<member id 2>' : [
                                        '<member id 1>',
                                        '<member id 2>'
                                    ]
                                },
                             '<insert member\'s account 1 id here>' : [
                                    '<insert account id 1 here>',
                                    '<insert account id 2 here>'
                                ],
                             '<insert member\'s account 2 id here>' : [
                                    '<insert account id 1 here>',
                                    '<insert account id 2 here>'
                                ]
                            }
            bot.data_man.save_json(accounts_info, accounts_filename)

    @commands.command(pass_context=True, hidden=True)
    @asyncio.coroutine
    def say(self, ctx):
        """ Makes the bot say something in a chosen channel.
            Usage: 'say <text>' or just 'say' if you want to give multiple
            messages in succession.
        """
        normal_rsp_timeout_sec = 40
        speaking_timeout_sec = 90

        server_list = [s for s in self.bot.servers]

        if len(server_list) == 0:
            yield from self.bot.say('I am not a member of any servers.')
            return

        # Find out what server to say in
        yield from self.bot.send_message(ctx.message.channel, 'Servers')
        yield from self.bot.send_message(ctx.message.channel, '-------')
        i = 1
        while i < len(server_list) + 1:
            yield from self.bot.send_message(ctx.message.channel,
                '{num}. {server}'.format(num=i, server=server_list[i-1].name))
            i += 1
        yield from self.bot.send_message(ctx.message.channel, '-------')

        server = None
        while not server:
            yield from self.bot.send_message(ctx.message.channel,
                'Please enter in a number for the server you want')
            message = yield from self.bot.wait_for_message(timeout=normal_rsp_timeout_sec,
                                                           channel=ctx.message.channel,
                                                           author=ctx.message.author)
            if not message:
                yield from self.bot.send_message(ctx.message.channel,
                    'You have taken too long to respond, please re-enter initial command.')
                return
            else:
                try:
                    num = int(message.content)
                    server = server_list[num-1]
                    del num
                except Exception:
                    yield from self.bot.send_message(ctx.message.channel,
                        'Invalid number, please try again.')

        # Find out what channel to say in
        channel_list = []
        for c in server.channels:
            if c.type != discord.ChannelType.voice:
                channel_list.append(c)

        yield from self.bot.send_message(ctx.message.channel, 'Channels')
        yield from self.bot.send_message(ctx.message.channel, '-------')
        i = 1
        while i < len(channel_list) + 1:
            yield from self.bot.send_message(ctx.message.channel,
                '{num}. {channel}'.format(num=i, channel=channel_list[i-1].name))
            i += 1
        yield from self.bot.send_message(ctx.message.channel, '-------')

        channel = None
        while not channel:
            yield from self.bot.send_message(ctx.message.channel,
                'Please enter in a number for the channel you want')
            message = yield from self.bot.wait_for_message(timeout=normal_rsp_timeout_sec,
                                                           channel=ctx.message.channel,
                                                           author=ctx.message.author)
            if not message:
                yield from self.bot.send_message(ctx.message.channel,
                    'You have taken too long to respond, please re-enter initial command.')
                return
            else:
                try:
                    num = int(message.content)
                    channel = channel_list[num-1]
                    del num
                except Exception:
                    yield from self.bot.send_message(ctx.message.channel,
                    'Invalid number, please try again.')

        # Say message(s)
        message = ctx.message.content[(len(ctx.prefix) + len(ctx.invoked_with)):]
        if message != '':
            yield from self.bot.send_message(channel, message)
        else:
            # Say messages as they are provided by the user
            begin_message = ('You may now type messages as much as you want,'
                ' and I will say them in the chosen channel. To stop,'
                ' simply wait {sec} seconds without doing anything, or type'
                ' \"exitcommand\" and I will stop mimicking what you say.')
            yield from self.bot.send_message(ctx.message.channel,
                begin_message.format(sec=speaking_timeout_sec))

            done_sending = False
            while not done_sending:
                message = yield from self.bot.wait_for_message(
                    timeout=speaking_timeout_sec,
                    channel=ctx.message.channel,
                    author=ctx.message.author)

                if not message or message.content.strip().lower() == 'exitcommand':
                    done_sending = True
                else:
                    yield from self.bot.send_message(channel, message.content)
            yield from self.bot.send_message(ctx.message.channel,
                'exiting command...')


def setup(bot):
    """ Allows this module to be added as an 'extension' to the bot. """
    bot.add_cog(Convenience(bot))
