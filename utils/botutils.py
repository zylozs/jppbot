from data.botsettings import ChannelType, InvalidCommandChannel, InvalidOwnerCommandChannel, UserNotAdmin, UserNotOwner, UserNotActive
from data.playerdata import UserNotRegistered
from utils.chatutils import SendMessage
from globals import *
from discord.ext import commands
import discord

def IsValidChannel(channelType:ChannelType, includeAdmin=True):
    async def predicate(ctx):
        # If we haven't setup an admin channel, allow the admin commands anywhere
        if (channelType == ChannelType.ADMIN and botSettings.adminChannel is None):
            return True

        if (not botSettings.IsValidChannel(ctx.channel, channelType, includeAdmin=includeAdmin)):
            raise InvalidCommandChannel(ctx.channel, channelType)
        return True
    return commands.check(predicate)

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
    async def predicate(ctx):
        if (not botSettings.IsUserAdmin(ctx.author)):
            raise UserNotAdmin(ctx.author)
        return True
    return commands.check(predicate)

def IsActivePlayer():
    async def predicate(ctx):
        if (not botSettings.IsUserRegistered(ctx.author)):
            raise UserNotRegistered(ctx.author)

        player = botSettings.GetRegisteredPlayerByID(ctx.author.id)
        if (player.matchesPlayed < 10):
            raise UserNotActive(ctx.author)
        return True
    return commands.check(predicate)

async def RemoveRoles(ctx, member, *rolesToRemove, errorMessage:str=''):
    try:
        await member.remove_roles(*rolesToRemove, reason='User {0.author} is updating roles for {1}'.format(ctx, member))
    except discord.HTTPException:
        await SendMessage(ctx, description=errorMessage, color=discord.Color.red())

async def AddRoles(ctx, member, *rolesToAdd, errorMessage:str=''):
    try:
        await member.add_roles(*rolesToAdd, reason='User {0.author} is updating roles for {1}'.format(ctx, member))
    except discord.HTTPException:
        await SendMessage(ctx, description=errorMessage, color=discord.Color.red())

