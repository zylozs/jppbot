from data.botsettings import ChannelType, InvalidCommandChannel, InvalidOwnerCommandChannel, UserNotAdmin, UserNotOwner, UserNotActive
from data.playerdata import UserNotRegistered
from utils.chatutils import SendChannelMessage, SendMessage
from globals import *
from discord import app_commands
from discord.ext import commands
from discord.utils import MISSING
import discord
import inspect

def GuildCommand(
    *,
    name: str = MISSING,
    description: str = MISSING,
):
    # Modified version of app_commands.command decorator. It will force the command to be a guild command 

    def decorator(func):
        if not inspect.iscoroutinefunction(func):
            raise TypeError('command function must be a coroutine function')

        if description is MISSING:
            if func.__doc__ is None:
                desc = '…'
            else:
                desc = app_commands.commands._shorten(func.__doc__)
        else:
            desc = description
    
        newCommand = app_commands.Command(
            name=name if name is not MISSING else func.__name__,
            description=desc,
            callback=func,
            parent=None,
            nsfw=False,
            auto_locale_strings=True,
            extras=MISSING,
        )

        newCommand.guild_only = True
        return newCommand

    return decorator

def IsValidChannel(channelType:ChannelType, includeAdmin=True):
    async def predicate(interaction:discord.Interaction):
        # If we haven't setup an admin channel, allow the admin commands anywhere
        if (channelType == ChannelType.ADMIN and botSettings.adminChannel is None):
            return True

        if (not botSettings.IsValidChannel(interaction.channel, channelType, includeAdmin=includeAdmin)):
            raise InvalidCommandChannel(interaction.channel, channelType)
        return True
    return app_commands.check(predicate)

def IsPrivateMessage():
    async def predicate(ctx):
        if (ctx.guild is not None):
            raise InvalidOwnerCommandChannel(ctx.channel)
        return True
    return commands.check(predicate)

def IsOwner():
    async def predicate(ctx):
        if (not botSettings.IsUserOwner(ctx.author)):
            raise UserNotOwner(ctx.author)
        return True
    return commands.check(predicate)

def IsAdmin():
    async def predicate(interaction:discord.Interaction):
        if (not botSettings.IsUserAdmin(interaction.user)):
            raise UserNotAdmin(interaction.user)
        return True
    return app_commands.check(predicate)

def IsActivePlayer():
    async def predicate(interaction:discord.Interaction):
        if (not botSettings.IsUserRegistered(interaction.user)):
            raise UserNotRegistered(interaction.user)

        player = botSettings.GetRegisteredPlayerByID(interaction.user.id)
        if (player.matchesPlayed < 10):
            raise UserNotActive(interaction.user)
        return True
    return app_commands.check(predicate)

async def RemoveRoles(interaction:discord.Interaction, member, *rolesToRemove, errorMessage:str=''):
    try:
        await member.remove_roles(*rolesToRemove, reason='User {0.user} is updating roles for {1}'.format(interaction, member))
    except discord.HTTPException:
        await SendChannelMessage(interaction.channel, description=errorMessage, color=discord.Color.red())

async def AddRoles(interaction:discord.Interaction, member, *rolesToAdd, errorMessage:str=''):
    try:
        await member.add_roles(*rolesToAdd, reason='User {0.user} is updating roles for {1}'.format(interaction, member))
    except discord.HTTPException:
        await SendChannelMessage(interaction.channel, description=errorMessage, color=discord.Color.red())

