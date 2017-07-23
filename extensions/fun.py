import asyncio
import logging
import random
import requests

import discord
from discord.ext import commands

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

def setup(bot):
    bot.add_cog(Fun(bot))