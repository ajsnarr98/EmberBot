import cacher
import message_parser
from utils import RestartRequired


class Command(object):
    """ Used when defining a command 
    
    Attributes
    ----------
    function:
        The function to run when the command starts
    description: str
        The description of the command
    subcommands: Optional[dict]
        A dictionary of {str : :class:'Command'} for subcommands

    incl_command_dict: bool
        Whenter or not to include the command_dict as an argument
    incl_auto_response_functions: bool
        Whether or not to include the list of auto_response_function

    """
    def __init__(self, function, description, subcommands=None,
                 incl_command_dict=False, incl_auto_response_functions=False):
        self._function = function
        self._description = description
        self._subcommands=subcommands

        self._incl_command_dict = incl_command_dict
        self._incl_auto_response_functions = incl_auto_response_functions

class AutoResponse(object):
    """ Used when defining a command 
    
    Attributes
    ----------
    function:
        The function to run when the command starts
    description: str
        The description of the command

    """
    def __init__(self, function, description):
        self._function = function
        self._description = description


"""
Command names and general messages to react to are defined
in message_parser.py, where as thier actual functions
are defined here.

Command functions MUST accept:
  - the parsed command message: :class:'ParsedMessage'
  - the client itself: :class:'discord.Client'
  - the logger

Auto-Response functions MUST accept:
  - the parsed command message: :class:'ParsedMessage'
  - the client itself: :class:'discord.Client'
  - the logger
AND MUST return:
  - true if the message meets the criteria to run the function
  - false if the message does not meets the criteria to run the function
"""

# ------------- COMMAND FUNCTIONS ------------------------

async def do_nothing(message, client, logger):
    pass
    # call help function
    # message.parsed_content = ['help'] + message.parsed_content
    # message.mes.content = 'help ' + message.mes.content

def list_sub_commands(sub_dict, cmd_description, base_cmd_name):
    """ Recursive function utilized in the 'help' function
        
        returns a string listing all commands in given sub_dict
        (part of command_dict), listing only the subcommands of
        commands that have the function 'do_nothing'
    """
    list_str = ''

    for name, cmd in sub_dict.items():
        if cmd._function == do_nothing and cmd._subcommands:
            list_str += list_sub_commands(
                cmd._subcommands,
                cmd_description,
                base_cmd_name + ' ' + name)
        else:
            list_str += cmd_description.format(
                base_cmd_name + ' ' + name,
                cmd._description)

    return list_str


async def help(message, client, logger, command_dict):
    """ Lists all commands, along with descriptions.

        Will list a command's subcommands if that command
        is specified as an argument, or in normal help list
        if that command's function is "do_nothing".

        Example: ":help music"

        If a command is given that does not have subcommands, a
        description for it will be listed.

        Example: ":help help"
    """

    spacesBeforeDescription = 15 # how much room command names can take up at max

    help_info = ''
    cmd = None
    legit_args = 0
    sub_dict = command_dict

    # Find a specified command or command group
    if len(message.parsed_content) > 1:
        cmd = True
        old_cmd = None
        old_sub_dict = None
        sub_dict = command_dict
        i = 1
        while i < len(message.parsed_content) and cmd and sub_dict:
            old_cmd = cmd
            cmd = sub_dict.get(message.parsed_content[i], None)
            if cmd:
                old_sub_dict = sub_dict
                sub_dict = cmd._subcommands

            i += 1

        if not cmd and old_cmd:
            cmd = old_cmd
        if not sub_dict and old_sub_dict:
            sub_dict = old_sub_dict

        legit_args = i - 1

    # ------- Create help string --------

    # Notify user about args that were not found
    if legit_args < (len(message.parsed_content) - 1):
        not_found_statment = 'Could not find command: {found_args}*{unfound_args}*\n\n'
        found_args = ''
        unfound_args = ''

        i = 1
        while i < len(message.parsed_content):
            if i <= (legit_args + 1):
                found_args += message.parsed_content[i] + ' '
            else:
                unfound_args += message.parsed_content[i] + ' '
            i += 1

        unfound_args.strip(' ')

        help_info += not_found_statment.format(found_args=found_args, unfound_args=unfound_args)

    # Fill in command description(s)
    cmd_description = '{0:12} - {1}\n'

    base_cmd_name = ''
    i = 1
    while i < (legit_args + 1):
        base_cmd_name += message.parsed_content[i] + ' '
        i += 1
    base_cmd_name.strip()

    if cmd: # if more than just 'help' was specified
        inv_sub_dict = {v: k for k, v in sub_dict.items()} # for getting names
        
        true_base_cmd_name = ''
        split = base_cmd_name.split(' ')
        i = 0
        while i < (len(split) - 2):
            true_base_cmd_name += split[i] + ' '
            i += 1
        true_base_cmd_name.strip()

        help_info += cmd_description.format(
            true_base_cmd_name + inv_sub_dict.get(cmd, ''),
            cmd._description)

        if cmd._subcommands:
            help_info += '\n'
    if not cmd or (cmd and cmd._subcommands): # if there is a list of commands to print
        if cmd and cmd._subcommands:
            sub_dict = cmd._subcommands # without this (if cmd == None), 
            #                             sub_dict is original command_dict
        
        # add list of commands in sub_dict
        help_info += list_sub_commands(sub_dict, cmd_description, base_cmd_name)

    # --------- Print help string ------------
    await client.send_message(
        message.mes.channel,
        help_info)


async def options(message, client, logger, auto_response_functions):
    """ Used for listing enabled/disabled auto-response functions

        Loads enabled/disabled values (bool objects) by accessing the cache
        with the key: "commands.options.{auto_response_function_name}"
    """

    auto_fucntion_str = '-----\n\"{name:15}\": {enabled};\n{descr}\n\n'
    cache_key = 'commands.options.{function_name}'

    for auto_function in auto_response_functions:
        is_enabled = cacher.get(
            cache_key.format(function_name=auto_function._function.__name__))
        enabled_str = ''
        if is_enabled == True or is_enabled == None:
            enabled_str = 'enabled'
        else:
            enabled_str = 'disabled'

        await client.send_message(
            message.mes.channel,
            auto_fucntion_str.format(
                name=auto_function._function.__name__,
                enabled=enabled_str,
                descr=auto_function._description))

def update_cache_auto_rsp(auto_response_functions):
    """ Updates the cache to make sure it has values for all auto-response-fucntions """
    cache_key = 'commands.options.{function_name}'

    for auto_function in auto_response_functions:
        is_enabled = cacher.get(
            cache_key.format(function_name=auto_function._function.__name__))

        if is_enabled == None:
            cacher.store(
                cache_key.format(function_name=auto_function._function.__name__),
                True)


async def options_enable(message, client, logger, auto_response_functions):
    """ Used for enabling auto-response functions

        Stores enabled/disabled values as bool objects that are
        stored in the cache with key "commands.options.{auto_response_function_name}"
    """
    update_cache_auto_rsp(auto_response_functions)

    cache_key = 'commands.options.{function_name}'

    if len(message.parsed_content) >= 3: # should be "options enable <function_name>"
        function_name = message.parsed_content[2]
        i = 3
        while i < len(message.parsed_content): # get remaining words for keys with spaces
            function_name += ' ' + message.parsed_content[i]
            i += 1

        key = cache_key.format(function_name=function_name)

        if cacher.get(key) != None: # if key is valid auto-response function
            #                        (works because of call to update_cache_auto_rsp)
            cacher.store(key, True)
            await client.send_message(
                message.mes.channel,
                function_name + ' has been enabled')
        else:
            await client.send_message(
                message.mes.channel,
                function_name + ' could not be found')
    else:
        await client.send_message(
            message.mes.channel,
            'Please give a valid option (\"options enable <option>\")')



async def options_disable(message, client, logger, auto_response_functions):
    """ Used for disabling auto-response functions

        Stores enabled/disabled values as bool objects that are
        stored in the cache with key "commands.options.{auto_response_function_name}"
    """
    update_cache_auto_rsp(auto_response_functions)

    cache_key = 'commands.options.{function_name}'

    if len(message.parsed_content) >= 3: # should be "options disable <function_name>"
        function_name = message.parsed_content[2]
        i = 3
        while i < len(message.parsed_content): # get remaining words for keys with spaces
            function_name += ' ' + message.parsed_content[i]
            i += 1

        key = cache_key.format(function_name=function_name)

        if cacher.get(key) != None: # if key is valid auto-response function
            #                        (works because of call to update_cache_auto_rsp)
            cacher.store(key, False)
            await client.send_message(
                message.mes.channel,
                function_name + ' has been disabled')
        else:
            await client.send_message(
                message.mes.channel,
                function_name + ' could not be found')
    else:
        await client.send_message(
            message.mes.channel,
            'Please give a valid option (\"options disable <option>\")')

        
async def restart(message, client, logger):
    """ Stops event loop and client by raising a RestartRequired exeption

        After the event loop ends, code in bot.py will restart the
        script (useful after an update for example)
    """
    logger.debug('attempting restart')
    await client.logout()

# ------------- AUTO-RESPONSE FUNCTIONS ------------------------

async def help_incorrect(message, client, logger):
    """ For when someone types 'help' without the command prefix """
    if message.mes.content.lower() == 'help':
        fmt = 'Did you mean \"{0}help\" ?'
        await client.send_message(
            message.mes.channel,
            fmt.format(message_parser.commandPrefix))

    return message.mes.content.lower() == 'help'

async def multi_account_mention(message, client, logger):
    """ A convenience function for users who have two accounts.
        If a user is @mentioned, and has two or more accounts,
        all his/her accounts will be @mentioned.
    """
    import accounts

    mentioned = False
    mention_str = '<@{id}>'
    output = ''

    for member in message.mes.mentions:
        if (accounts.accountMap.get(member.id, None)): # if member id in dict
            for account_id in accounts.accountMap.get(member.id, None):
                output += mention_str.format(id=account_id) + ' '

    if output != '':
        await client.send_message(
            message.mes.channel,
            output)

    return mentioned