import asyncio
import datetime
import logging
import random
import requests
import time

import discord
from discord.ext import commands

from .core import AutoResponse, auto_response

class Fun():
    """ Filled with fun commands for the bot. """

    def __init__(self, bot):
        self.bot = bot
        self.data_man = bot.data_man
        self.logger = logging.getLogger('discord')

    @commands.command(name='8ball')
    @asyncio.coroutine
    def eight_ball(self, message : str):
        """ Usage: '8ball <question>'

            Gives a random 8ball response to the provided question.
        """
        eight_ball_filename = '8ball.json'

        responses = self.data_man.load_json(eight_ball_filename)
        response_list = None
        response_emoji_list = None

        if responses:
            response_list = responses.get('response_list', None)
            response_emoji_list = responses.get('emoji_list', None)
        else:
            response_emoji_list = [':blush:',
                                   ':smirk:',
                                   ':ok_hand:',
                                   ':thinking_face:',
                                   ':rolling_eyes:']
            response_list = ['It is certain',
                             'It is decidedly so',
                             'Without a doubt',
                             'Yes definitely',
                             'You may rely on it',
                             'As I see it, yes',
                             'Most likely',
                             'Outlook good',
                             'Yes',
                             'Signs point to yes',
                             'Reply hazy try again',
                             'Ask again later',
                             'Better not tell you now',
                             'Cannot predict now',
                             'Concentrate and ask again',
                             'Don\'t count on it',
                             'My reply is no',
                             'My sources say no',
                             'Outlook not so good',
                             'Very doubtful']

            responses = {'response_list' : response_list, 
                         'emoji_list' : response_emoji_list}

            self.data_man.save_json(responses, eight_ball_filename)

        response = '[**8Ball**] :crystal_ball: {0} {1}'.format(
            random.choice(response_list), random.choice(response_emoji_list))

        yield from self.bot.say(response)

    @commands.command(aliases=['chuck'])
    @asyncio.coroutine
    def chucknorris(self):
        """ Want to know some interesting Chuck Norris facts? """
        joke_msg = '[**Chuck**] {joke}'

        chuckPull = requests.get('http://api.icndb.com/jokes/random')
        if chuckPull and chuckPull.status_code  == 200:
            joke = chuckPull.json()['value']['joke']
            yield from self.bot.say(joke_msg.format(joke=joke))

    @auto_response()
    @asyncio.coroutine
    def auto_pong(self, bot, message):
        """ Says 'pong' when someone says 'ping' in the chat. """
        if message.content.lower() == 'ping':
            yield from bot.send_message(message.channel, 'pong')

    @commands.command(pass_context=True)
    @asyncio.coroutine
    def ping(self, ctx):
        """ Reply with a pong! Used to test response time. """
        response = ':ping_pong: Pong: {response_desc}'

        epoch = datetime.datetime.utcfromtimestamp(0)
        time_of_message = (ctx.message.timestamp - epoch).total_seconds()
        now = time.time()

        response_sec = int((now - time_of_message))

        response_desc = None
        if response_sec <= 1:
            response_desc = '< 1s'
        else:
            response_desc = '> {}s'.format(response_sec)

        embed = discord.Embed(colour=discord.Colour.light_grey(),
                              title=response.format(response_desc=response_desc))

        yield from self.bot.send_message(ctx.message.channel, embed=embed)

def setup(bot):
    bot.add_cog(Fun(bot))