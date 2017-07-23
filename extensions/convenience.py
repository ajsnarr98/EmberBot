import asyncio

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
            fmt = 'Did you mean \"{0}help\" ?'
            
            prefix = bot.default_command_prefix

            yield from bot.send_message(
                message.channel,
                fmt.format(prefix))


def setup(bot):
    """ Allows this module to be added as an 'extension' to the bot. """
    bot.add_cog(Convenience(bot))
