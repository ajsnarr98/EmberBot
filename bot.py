import asyncio
import logging
import os
import sys
import time
import traceback

import discord

import accounts
import message_parser
import secret
import self_updater
from utils import RestartRequired


# set up logger
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# define parser variable; initialize as MessageParser
parser = None

class DiscordBot(discord.Client):

    def __init__(self, *args, loop=None, **options):
        super().__init__(*args, loop=None, **options)
        self.parser = message_parser.MessageParser(self, logger)

    async def on_ready(self):
        print('Connected!')
        print('Username: ' + self.user.name)
        print('ID: ' + self.user.id)

    async def on_message(self, message):
        if message.author != self.user: # do not want bot to reply to self
            await self.parser.parse_and_react(message)

    def restart(self):
        """ Restarts after event loop has ended, and checks for updates """
        seconds_before_restart = 5

        self_updater.restart(logger, seconds_before_restart=seconds_before_restart)


    def run(self, *args, **kwargs):
        """ 
        Can call commands.restart() to stop event loop """

        restart = True

        try:
            self.loop.run_until_complete(self.start(*args, **kwargs))

        except KeyboardInterrupt:
            self.loop.run_until_complete(self.logout())
            pending = asyncio.Task.all_tasks(loop=self.loop)
            gathered = asyncio.gather(*pending, loop=self.loop)
            try:
                gathered.cancel()
                self.loop.run_until_complete(gathered)

                # we want to retrieve any exceptions to make sure that
                # they don't nag us about it being un-retrieved.
                gathered.exception()
            except:
                pass
            # do not want to restart if given a KeyboardInterrupt
            restart = False
        except SystemExit:
            restart = False
        finally:
            self.loop.close()
            if restart:
                self.restart()


if __name__ == '__main__':
    bot = DiscordBot()
    bot.run(secret.botToken)