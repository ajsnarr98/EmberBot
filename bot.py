if __name__ == '__main__':
    import dependencies
    dependencies.install() # attempt to isntall any missing dependencies

import asyncio
import inspect
import logging
import os
import sys
import time
import traceback

import discord
from discord.ext import commands

from extensions.core import AutoResponse
from extensions.data import DataManager
import secret
import self_updater

# set up logger
log_filename = 'discord.log'
working_dir = os.path.dirname(os.path.abspath(__file__))
log_filename = os.path.join(working_dir, log_filename)
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=log_filename, encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


class DiscordBot(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_command_prefix = kwargs.get('default_command_prefix', None)
        self.auto_responses = []
        self.data_man = DataManager()

    @asyncio.coroutine
    def on_ready(self):
        print('Connected!')
        print('Username: ' + self.user.name)
        print('ID: ' + self.user.id)
        print('------')

        yield from self.say_in_all('''I'm back and better than ever!''')

        yield from self.change_presence(
            game=discord.Game(name='{}help for commands.'.format(self.default_command_prefix)))
        
        self.load_extension('extensions.core')
        self.load_extension('extensions.convenience')

    def add_auto_response(self, auto_response):
        """Adds a :class:`extensions.core.AutoResponse` into the internal list
        of auto responses.

        Parameters
        -----------
        auto_response
            The auto response to add.
        Raises
        -------
        discord.ClientException
            If the auto response is already registered.
        TypeError
            If the auto response passed is not a subclass of
            :class:`extensions.core.AutoResponse`.
        """

        if not isinstance(auto_response, AutoResponse):
            raise TypeError('The auto response passed must be a subclass of AutoResponse')

        if auto_response.name in self.auto_responses:
            raise discord.ClientException('AutoResponse {0.name} is already registered.'.format(auto_response))

        self.auto_responses.append(auto_response)

    def add_cog(self, cog):
        super().add_cog(cog)

        members = inspect.getmembers(cog)
        for name, member in members:
            # register auto-responses the cog has
            if isinstance(member, AutoResponse):
                self.add_auto_response(member)

    @asyncio.coroutine
    def say_in_all(self, *args, **kwargs):
        """ A helper function that is equivalent to doing

        .. code-block:: python
    
            for channel in <one channel on every server>:
                self.send_message(channel, *args, **kwargs)

        """
        for server in self.servers:
            done_one_channel = False
            for channel in server.channels:
                if done_one_channel:
                    break
                yield from self.send_message(channel, *args, **kwargs)
                done_one_channel = True

    @asyncio.coroutine
    def process_auto_responses(self, message):
        """ This function sorts through all auto-responses that have been
            registered, and runs all that are enabled.
        """
        auto_rsp_json = self.data_man.load_json(AutoResponse.saveFile)
        for auto_response in self.auto_responses:
            this_json = auto_rsp_json.get(auto_response.name, None)
            if this_json:
                if this_json.get('enabled', False):
                    yield from auto_response.callback(self, self, message)

    @asyncio.coroutine
    def on_message(self, message):
        yield from self.process_commands(message)
        yield from self.process_auto_responses(message)

    @asyncio.coroutine
    def on_command_error(self, exception, context):
        """ Logs and ignores errors in commands, unless that exception was from
            entering an invalid command, in which case this instead tells the
            user that they gave an invalid command.
        """
        if type(exception) == commands.errors.CommandNotFound:
            yield from self.send_message(context.message.channel, str(exception))
        else:
            logger.error('Ignoring exception in command {}'.format(context.command))
            print('Ignoring exception in command {}'.format(context.command), file=sys.stderr)
            traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)

    def _restart(self):
        """ Restarts after event loop has ended, and checks for updates """
        seconds_before_restart = 5

        self_updater.check_for_updates()
        self_updater.restart(logger, seconds_before_restart=seconds_before_restart)

    def run(self, *args, **kwargs):
        """ 
        Can call 'update' command, or self.loggout to stop event loop """

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
                self._restart()

def get_command_prefix(bot, message):
    """ Returns list of command prefixes, plus a prefix for when a message mentions the bot. """
    prefixes = [':']
    prefix_list = commands.when_mentioned_or(*prefixes)(bot, message)
    return prefix_list

default_command_prefix = ':'

if __name__ == '__main__':
    description = ''' A bot to fulfill your wildest dreams. '''
    bot = DiscordBot(get_command_prefix, description=description, pm_help=False, default_command_prefix=default_command_prefix)
    bot.run(secret.botToken)