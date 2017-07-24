import asyncio
import copy
import functools
import inspect
import json
import logging

import discord
from discord.ext import commands

from .data import DataManager

def check_is_admin():
    """ A decorator that checks if a given command was run by an 'admin' """
    def predicate(ctx):
        # only one of these role names or perms is needed to be 'admin'
        admin_role_names = ('Admin', 'Moderator', 'bot_admin')
        admin_role_perms = {'administrator' : True}

        msg = ctx.message
        ch = msg.channel
        if ch.is_private:
            return False

        permissions = ch.permissions_for(msg.author)

        role_getter = functools.partial(discord.utils.get, msg.author.roles)
        has_role = any(role_getter(name=name) is not None for name in admin_role_names)
        has_perms = all(getattr(permissions, perm, None) == value for perm, value in admin_role_perms.items())
        return has_role or has_perms

    return commands.check(predicate)

class Core():
    """ Filled with core commands for the bot. """

    def __init__(self, bot):
        self.bot = bot
        self.data_man = bot.data_man
        self.logger = logging.getLogger('discord')

    @commands.command(aliases=['restart'], help='Restarts bot and checks for updates.')
    @asyncio.coroutine
    def update(self):
        """  Stops event loop and client by logging the bot out.
        After the event loop ends, the bot will check for
        updates and restart this script.
        """
        self.logger.debug('attempting restart')
        yield from self.bot.say_in_all('restarting...')
        yield from self.bot.logout()

    @commands.group(pass_context=True, brief='Please see \'help settings\' for more info.')
    @asyncio.coroutine
    def settings(self, ctx):
        """ A group of commands for managing the bot. """
        if not ctx.invoked_subcommand:
            response = 'Please use \"{prefix}help settings\" for a list of commands.'
            prefix = ctx.prefix
            yield from self.bot.say(response.format(prefix=prefix))

    @settings.command(pass_context=True, name='list')
    @asyncio.coroutine
    def _list(self, ctx):
        """ Displays a list of editable settings. """
        paginator = commands.Paginator()

        for dirpath, dirnames, filenames in self.data_man.walk_json():
            for filename in filenames:
                no_ext = filename.split('.')[0] # remove filename extension
                paginator.add_line(line='-- \'{0}\''.format(no_ext))
        
        pages = paginator.pages
        for p in pages:
            yield from self.bot.say(p)

    @settings.command(pass_context=True, name='edit')
    #@check_is_admin()
    @asyncio.coroutine
    def _edit(self, ctx, setting : str):
        """ Use 'settings edit <setting>'.
            
            Used for editing a given setting. Can see settings
            through 'settings list'.

            WARNING: Only people who the bot recognises as 'admins'
                     can use this command.
        """
        normal_rsp_timeout_sec = 40
        edit_timeout_sec = 120

        filename = setting + '.json'
        setting_obj = self.data_man.load_json(filename)
        if not setting_obj:
            yield from self.bot.say('No setting called \'{0}\' found. Please use \'settings list\'.'.format(setting))
        else:
            setting_json = json.dumps(setting_obj, indent=2)
            rsp_channel = None
            if ctx.message.channel.is_private:
                channel = ctx.message.channel
            else:
                channel = yield from self.bot.start_private_message(ctx.message.author)

            paginator = commands.Paginator()
            paginator.add_line(filename)
            paginator.close_page()
            paginator.add_line(setting_json)
            for p in paginator.pages:
                yield from self.bot.send_message(channel, p)

            done_waiting_for_rsp = False
            yield from self.bot.send_message(channel, 'Is this the file you want to edit? [Y/N]?')
            while not done_waiting_for_rsp:
                message = yield from self.bot.wait_for_message(timeout=normal_rsp_timeout_sec,
                                                               channel=channel)
                if not message:
                    yield from self.bot.send_message(channel,
                        'You have taken too long to respond, please re-enter initial command.')
                    done_waiting_for_rsp = True
                    return
                elif message.author != self.bot.user:
                    if message.content.lower().startswith('y'):
                        yield from self.bot.send_message(channel,
                        'Ok! Please send an edited version of the above file to change settings :smiley:.' +
                        ' Make sure the format is valid!')
                        done_waiting_for_rsp = True
                    elif message.content.lower().startswith('n'):
                        yield from self.bot.send_message(channel,
                        'Ok. If you meant another file, go ahead and just re-enter the command. Exiting command now')
                        done_waiting_for_rsp = True
                        return
                    else:
                        yield from self.bot.send_message(channel,
                        'Sorry, I couldn\'t read that. Please enter either \'y\' or \'n\'. :smiley:')
                del message
            del done_waiting_for_rsp

            done_waiting_for_rsp = False
            while not done_waiting_for_rsp:
                message = yield from self.bot.wait_for_message(timeout=edit_timeout_sec,
                                                               channel=channel)
                if not message:
                    yield from self.bot.send_message(channel,
                        'You have taken too long to respond, please re-enter initial command...')
                    done_waiting_for_rsp = True
                    return
                elif message.author != self.bot.user:
                    if message.content.lower() == 'exit':
                        yield from self.bot.send_message(channel,
                            'Canceling command...')
                        done_waiting_for_rsp = True
                        return
                    else:
                        json_obj = None
                        try:
                            json_obj = json.loads(message.content)
                        except ValueError: # will be json.decoder.JSONDecodeError
                            #                instead of ValueError in python 3.6 (instead of 3.4)
                            yield from self.bot.send_message(channel,
                                'I\'m sorry I couldn\'t read that! If it helps,' +
                                ' the text needs to be in valid JSON format. Try re-entering' +
                                ' the text, or type \'exit\' or just do nothing for a bit if you want to stop.')
                            del message
                            continue
                        if json_obj:
                            self.bot.data_man.save_json(json_obj, filename)
                            yield from self.bot.send_message(channel,
                                'Settings have been updated! Exiting command now...')
                            yield from self.bot.send_message(channel,
                                ' :warning: I will warn you though... If something breaks pretty soon,' +
                                ' you might want to check back here and see if you changed' + 
                                ' everything correctly...')
                            done_waiting_for_rsp = True
                del message
            del done_waiting_for_rsp

def setup(bot):
    """ Allows this module to be added as an 'extension' to the bot. """
    bot.add_cog(Core(bot))

class AutoResponse(object):
    """ This class represents a coroutine that will be called when 
        a message is received by the bot. This coroutine should only
        perform its functions when varying conditions are met in that
        message.

        Attributes
        -----------
        name : str
            The name of the auto-response. Is the same as callback.__name__.
        callback : coroutine
            The coroutine that is executed when the auto-response is enabled.
            This coroutine must take in the args: (bot, message) and must
            return if either of those args do not meet the function's conditions.
        description : str
            The description for this auto-response.
        default_enabled: bool
            A boolean that indicates if the auto-response is enabled by
            default. Defaults to True.
        no_pm : bool
            If ``True``\, then the auto-response will not be triggered in
            private messages. Defaults to ``False``.
        enabled : bool
            A boolean that indicates if the auto-response is currently enabled.
            When disabled, the auto-response can never be triggered.
        json : str
            A str in json format containing the AutoResponse name, description,
            and whether or not it is enabled.

        Raises
        -------
        AttributeError
            If the description is not given (aka. if there is no doc or no set
            description).
    """

    saveFile = 'auto_responses.json'

    def __init__(self, callback, description=None, **attrs):
        if description == None:
            raise AttributeError('AutoResponse must have a description')

        self.callback = callback
        self.description = description
        self.no_pm = attrs.get('no_pm', False)

        self.data_man = DataManager()

        self.try_to_enable(attrs.get('default_enabled', True))

    def try_to_enable(self, default_enabled : bool):
        """ Enables or disables this AutoResponse, and updates the setting in
            the AutoResponse.saveFile data file.
        """
        auto_rsp_json = self.data_man.load_json(AutoResponse.saveFile)
        if not auto_rsp_json or auto_rsp_json == '':
            self._enabled = default_enabled
            auto_rsp_json = {self.name : self.json_dict}
        else:
            this_json = auto_rsp_json.get(self.name, None)
            if this_json:
                self._enabled = this_json.get('enabled', default_enabled)
                auto_rsp_json[self.name] = self.json_dict
            else:
                self._enabled = default_enabled
                auto_rsp_json[self.name] = self.json_dict
        self.data_man.save_json(auto_rsp_json, AutoResponse.saveFile)

    @property
    def name(self):
        return self.callback.__name__

    @property
    def enabled(self):
        return self._enabled

    @property
    def json(self):
        return json.dumps(self.simple_dict)

    @property
    def json_dict(self):
        simple_dict = {'name' : self.name,
                       'enabled' : self.enabled,
                       'description' : self.description}
        return simple_dict


def auto_response(**attrs):
    """ A decorator that transforms a fucntion into a :class:`AutoResponse`.

        By default the ``help`` attribute is received automatically from the
        docstring of the function and is cleaned up with the use of
        ``inspect.cleandoc``. If the docstring is ``bytes``, then it is decoded
        into ``str`` using utf-8 encoding.

        Raises
        -------
        TypeError
            If the function is not a coroutine.
    """

    def decorator(func):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError('Callback must be a coroutine.')

        # Eventually cooldown stuff may go here

        # get description
        description = attrs.get('description', None)
        if description is not None:
            description = inspect.cleandoc(description)
            description = description.replace('\n', ' ') # remove all newline chars
        else:
            description = inspect.getdoc(func)
            if isinstance(description, bytes):
                description = description.decode('utf-8')
            description = description.replace('\n', ' ') # remove all newline chars

        return AutoResponse(func, description, **attrs)

    return decorator