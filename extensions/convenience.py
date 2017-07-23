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


def setup(bot):
    """ Allows this module to be added as an 'extension' to the bot. """
    bot.add_cog(Convenience(bot))
