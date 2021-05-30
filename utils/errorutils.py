from data.botsettings import ChannelTypeInvalid, GuildTextChannelMismatch, GuildRoleMismatch, RegisteredRoleUnitialized, AdminRoleUnitialized, InvalidGuild, InvalidCommandChannel, UserNotAdmin
from data.mmrrole import InvalidMMRRole, MMRRoleExists, MMRRoleRangeConflict, NoMMRRoles
from data.siegemap import MapExists, InvalidMap 
from data.playerdata import UserNotRegistered, UserAlreadyRegistered
from data.matchhistorydata import InvalidMatchResult, MatchIDNotFound, MatchResultIdentical
from services.matchservice import PlayerAlreadyQueued, PlayerNotQueued
from utils.chatutils import SendMessage

from discord.ext import commands
import discord

async def HandleError(ctx, error):
	print('Error: {}'.format(error))
	if (isinstance(error, commands.ChannelNotFound)):
		await SendMessage(ctx, description='`{}` is not a valid text channel.'.format(error.argument), color=discord.Color.red())

	elif (isinstance(error, commands.RoleNotFound)):
		await SendMessage(ctx, description='`{}` is not a valid role.'.format(error.argument), color=discord.Color.red())

	elif (isinstance(error, commands.MemberNotFound)):
		await SendMessage(ctx, description='Member not found. You can use their display name (case sensitive), id, or @ them.'.format(), color=discord.Color.red())

	elif (isinstance(error, commands.CommandNotFound)):
		await SendMessage(ctx, description='{} is not a valid command.'.format(error.argument), color=discord.Color.red())

	elif (isinstance(error, ChannelTypeInvalid)):
		await SendMessage(ctx, description='`{}` is not a valid channel type.'.format(error.argument), color=discord.Color.red())

	elif (isinstance(error, RegisteredRoleUnitialized)):
		await SendMessage(ctx, description='The registered role has not been setup yet.', color=discord.Color.red())

	elif (isinstance(error, AdminRoleUnitialized)):
		await SendMessage(ctx, description='The admin role has not been setup yet.', color=discord.Color.red())

	elif (isinstance(error, GuildTextChannelMismatch)):
		await SendMessage(ctx, description='`{0.mention}` is not in the same server as the other text channels'.format(error.argument), color=discord.Color.red())

	elif (isinstance(error, GuildRoleMismatch)):
		await SendMessage(ctx, description='`{0.mention}` is not in the same server as the text channels'.format(error.argument), color=discord.Color.red())

	elif (isinstance(error, InvalidMMRRole)):
		await SendMessage(ctx, description='{0.mention} is not a valid rank.'.format(error.argument), color=discord.Color.red())

	elif (isinstance(error, MMRRoleExists)):
		await SendMessage(ctx, description='{0.mention} is already a rank.'.format(error.argument), color=discord.Color.red())

	elif (isinstance(error, MMRRoleRangeConflict)):
		await SendMessage(ctx, description='The MMR Range you provided overlaps with another rank.', color=discord.Color.red())

	elif (isinstance(error, MapExists)):
		await SendMessage(ctx, description='{} is already a map'.format(error.argument), color=discord.Color.red())

	elif (isinstance(error, InvalidMap)):
		await SendMessage(ctx, description='{} is not a valid map.'.format(error.argument), color=discord.Color.red())

	elif (isinstance(error, InvalidGuild)):
		await SendMessage(ctx, description='There is no guild set.', color=discord.Color.red())

	elif (isinstance(error, InvalidMatchResult)):
		await SendMessage(ctx, description='`{}` is not a valid Match Result.'.format(argument), color=discord.Color.red())

	elif (isinstance(error, NoMMRRoles)):
		await SendMessage(ctx, description='There are no ranks.', color=discord.Color.red())

	elif (isinstance(error, PlayerAlreadyQueued)):
		await SendMessage(ctx, description='You are already in queue.', color=discord.Color.red())

	elif (isinstance(error, PlayerNotQueued)):
		await SendMessage(ctx, description='You are not currently in queue.', color=discord.Color.red())

	elif (isinstance(error, InvalidCommandChannel)):
		await SendMessage(ctx, description='{0.mention} is not the correct channel for {1.value} commands.'.format(error.argument, error.type), color=discord.Color.red())

	elif (isinstance(error, UserNotRegistered)):
		await SendMessage(ctx, description='User {0.mention} is not registered'.format(error.argument), color=discord.Color.red())

	elif (isinstance(error, UserAlreadyRegistered)):
		await SendMessage(ctx, description='User {0.mention} is already registered'.format(error.argument), color=discord.Color.red())

	elif (isinstance(error, MatchIDNotFound)):
		await SendMessage(ctx, description='Match with id `{}` was not found. The match history either doesn\'t exist for this match or this is not a valid match id.'.format(error.argument), color=discord.Color.red())

	elif (isinstance(error, MatchResultIdentical)):
		await SendMessage(ctx, description='The new match result is the same as the original. Nothing will happen.', color=discord.Color.red())

	elif (isinstance(error, UserNotAdmin)):
		await SendMessage(ctx, description='You do not have permission to run this command.', color=discord.Color.red())

	elif (isinstance(error, commands.errors.MissingRequiredArgument)):
		await SendMessage(ctx, description='Invalid usage: `{0.name}` is a required argument'.format(error.param), color=discord.Color.red())

	elif (isinstance(error, commands.BadArgument)):
		await SendMessage(ctx, description='Bad Argument: {}'.format(error), color=discord.Color.red())

