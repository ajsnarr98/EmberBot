import asyncio

import cacher
from commands import Command, AutoResponse
import commands

commandPrefix = ':'

command_dict = {
            #'help' : Command(commands.help, 'Lists commands', incl_command_dict=True),
            'options' : Command(commands.options,
                'Lists options. Can also be used in format: ' + 
                '\"options [enable/disable] <option>\" See "help ' +
                'options" for more',
                incl_auto_response_functions=True,
                subcommands={
                'enable' : Command(commands.options_enable,
                    '\"options enable <option>\"',
                    incl_auto_response_functions=True),
                'disable' : Command(commands.options_disable,
                    '\"options disable <option>\"',
                    incl_auto_response_functions=True)
                })
            #'restart' : Command(commands.restart, 'Restarts the bot')
        }

auto_response_functions = [
            AutoResponse(commands.help_incorrect, 'Respond when someone types \"help\"'),
            AutoResponse(commands.multi_account_mention,
                   'When someone with mulitple accounts is @mentioned, ' + 
                   '@mentiones all his/her accounts'
                )
            ]

"""
command_dict:
    A dictionary of {str : :class:'Command'} where the str key
    represents the command or start of the command (after the
    command prefix), and the value contains a description for it,
    as well as the function to call, and any sub-commands.
    Str keys CANNOT have spaces (spaces seperate commands and sub-commands).

auto_response_functions:
    A list of functions that, once called, either return true because a condition
    for them to run is met, or false because they will not run.
"""

class ParsedMessage(object):
    """ Represents a parsed version of an incoming message,
        with command prefix removed and all words split at spaces.

        Attributes
        ----------
        mes: :class:'discord.Message'
            the original message
        is_command: bool
            whether or not the message started with
            the command prefix
        parsed_content: list
            a list of words split by spaces
    """

    def __init__(self, message):
        """ message: :class:'discord.Message' """
        self.mes = message

        content = ''
        if message.content.startswith(commandPrefix):
            self.is_command = True
            # remove prefix
            content = message.content.lower()[len(commandPrefix):]
        else:
            self.is_command = False
            content = message.content.lower()

        self.parsed_content = content.strip(' ').split(' ')

class MessageParser(object):
    """ Runs the respective command or function for each respective message

    Attributes
    ----------
    client: :class:'discord.Client'
        Client that acts as the bot
    """

    def __init__(self, client, logger):
        self.client = client
        self.logger = logger

    @asyncio.coroutine
    def parse_and_react(self, message):
        """ Runs the respective command or function for each respective message """
        parsed = ParsedMessage(message)

        if parsed.is_command:
            if (parsed.parsed_content[0]) == 'help' or parsed.parsed_content[0] == '':
                # yield from command_dict['help']._function(parsed, self.client, self.logger,
                #     command_dict)
                pass
            else:
                cmd = self.get_command(parsed.parsed_content)
                if cmd and cmd._function:
                    function = cmd._function

                    
                    if cmd._incl_command_dict and cmd._incl_auto_response_functions:
                        yield from function(parsed, self.client, self.logger,
                            command_dict, auto_response_functions)
                    elif cmd._incl_command_dict:
                        yield from function(parsed, self.client, self.logger, command_dict)
                    elif cmd._incl_auto_response_functions:
                        yield from function(parsed, self.client, self.logger,
                            auto_response_functions)
                    else:
                        yield from function(parsed, self.client, self.logger)

        else:
            # For reactions to messages that do not start with the command prefix
            # (check if enabled first)
            cache_key = 'commands.options.{function_name}'
            for auto_function in auto_response_functions:
                function = auto_function._function
                is_enabled = cacher.get(cache_key.format(function_name=function.__name__))
                if is_enabled == None: # if is not in cache, put in cache with default
                    #                    value of true
                    cacher.store(
                        cache_key.format(function_name=function.__name__),
                        True)
                    is_enabled = True
                
                if is_enabled:
                    yield from function(parsed, self.client, self.logger)




    def get_command(self, parsed_content):
        """ Return the command from command_dict for given parsed command
        
        parsed_content: list[str]
            the parsed_content attribute of a ParsedMessage object

        returns the specified command, or None if it does not exist
        """
        cmd = True
        old_cmd = None
        sub_dict = command_dict
        i = 0
        while i < len(parsed_content) and cmd and sub_dict:
            old_cmd = cmd
            cmd = sub_dict.get(parsed_content[i], None)
            if cmd:
                sub_dict = cmd._subcommands

            i += 1

        # old_cmd is the last command in the list that was in
        # its respective section of command_dict
        if not cmd and old_cmd:
            cmd = old_cmd

        if type(cmd) == commands.Command:
            return cmd
        else:
            return None

