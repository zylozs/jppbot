from data.botsettings import ChannelTypeInvalid, GuildTextChannelMismatch, GuildRoleMismatch, InvalidChannelType, InvalidRole, RegisteredRoleUnitialized, AdminRoleUnitialized, InvalidGuild, InvalidCommandChannel, InvalidOwnerCommandChannel, UserNotAdmin, UserNotOwner, EmptyName, InvalidActivityIndex, InvalidQuipIndex, EmptyQuip, InvalidStratIndex, UserNotActive
from data.mmrrole import InvalidMMRRole, MMRRoleExists, MMRRoleRangeConflict, NoMMRRoles
from data.siegemap import CantRerollMap, MapExists, InvalidMap 
from data.playerdata import UserNotRegistered, UserAlreadyRegistered
from data.matchhistorydata import InvalidMatchResult, MatchIDNotFound, MatchResultIdentical
from data.activitydata import InvalidActivityType, NoActivities
from data.quipdata import NoQuips, InvalidQuipType, InvalidGuildEmoji
from data.mappool import CantForceMapPool, InvalidMapPool, MapPoolExists, InvalidMapPoolType, InvalidMapPoolMap, MapPoolMapExists
from data.stratroulettedata import InvalidStratRouletteTeamType, NoStratRouletteStrats, EmptyStrat
from services.matchservice import PlayerAlreadyQueued, PlayerNotQueued, PlayerNotQueuedOrInGame, PlayersNotSwapable, PlayerSwapFailed
from utils.chatutils import SendMessage

from discord.ext import commands
import discord
from discord import app_commands

class NoPrivateMessages(commands.CheckFailure):
    def __init__(self):
        super().__init__('You can\'t run commands in dms.')

async def HandleAppError(interaction:discord.Interaction, error:app_commands.AppCommandError):
    print('Error: {}'.format(error.original))
    if (isinstance(error.original, commands.ChannelNotFound)):
        await SendMessage(interaction, description='`{}` is not a valid text channel.'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, commands.RoleNotFound)):
        await SendMessage(interaction, description='`{}` is not a valid role.'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, commands.UserNotFound)):
        await SendMessage(interaction, description='User not found. You can use their display name (case sensitive), id, or @ them.'.format(), color=discord.Color.red())

    elif (isinstance(error.original, commands.MemberNotFound)):
        await SendMessage(interaction, description='Member not found. You can use their display name (case sensitive), id, or @ them.'.format(), color=discord.Color.red())

    elif (isinstance(error.original, commands.CommandNotFound)):
        await SendMessage(interaction, description='{} is not a valid command.'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, ChannelTypeInvalid)):
        await SendMessage(interaction, description='`{}` is not a valid channel type.'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, RegisteredRoleUnitialized)):
        await SendMessage(interaction, description='The registered role has not been setup yet.', color=discord.Color.red())

    elif (isinstance(error.original, AdminRoleUnitialized)):
        await SendMessage(interaction, description='The admin role has not been setup yet.', color=discord.Color.red())

    elif (isinstance(error.original, GuildTextChannelMismatch)):
        await SendMessage(interaction, description='`{0.mention}` is not in the same server as the other text channels'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, GuildRoleMismatch)):
        await SendMessage(interaction, description='`{0.mention}` is not in the same server as the text channels'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, InvalidMMRRole)):
        await SendMessage(interaction, description='{0.mention} is not a valid rank.'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, InvalidActivityIndex)):
        await SendMessage(interaction, description='{0} is not a valid activity index.'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, InvalidQuipIndex)):
        await SendMessage(interaction, description='{0} is not a valid quip index.'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, InvalidStratIndex)):
        await SendMessage(interaction, description='{0} is not a valid Strat Roulette strat index.'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, InvalidGuildEmoji)):
        await SendMessage(interaction, description='{0} is not a valid guild emoji.'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, MMRRoleExists)):
        await SendMessage(interaction, description='{0.mention} is already a rank.'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, MMRRoleRangeConflict)):
        await SendMessage(interaction, description='The MMR Range you provided overlaps with another rank.', color=discord.Color.red())

    elif (isinstance(error.original, MapExists)):
        await SendMessage(interaction, description='`{}` is already a map'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, InvalidMap)):
        await SendMessage(interaction, description='`{}` is not a valid map.'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, MapPoolExists)):
        await SendMessage(interaction, description='`{}` is already a map pool'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, InvalidMapPool)):
        await SendMessage(interaction, description='`{}` is not a valid map pool.'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, MapPoolMapExists)):
        await SendMessage(interaction, description='`{}` is already a map in `{}`'.format(error.original.argument2, error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, InvalidMapPoolMap)):
        await SendMessage(interaction, description='`{}` is not a valid map in `{}`.'.format(error.original.argument2, error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, CantForceMapPool)):
        await SendMessage(interaction, description='You can\'t force a map pool when a match isn\'t running.', color=discord.Color.red())

    elif (isinstance(error.original, CantRerollMap)):
        await SendMessage(interaction, description='You can\'t reroll a map when a match isn\'t running.', color=discord.Color.red())

    elif (isinstance(error.original, InvalidGuild)):
        await SendMessage(interaction, description='There is no guild set.', color=discord.Color.red())

    elif (isinstance(error.original, InvalidMatchResult)):
        await SendMessage(interaction, description='`{}` is not a valid Match Result.'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, InvalidActivityType)):
        await SendMessage(interaction, description='`{}` is not a valid Activity Type.'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, InvalidMapPoolType)):
        await SendMessage(interaction, description='`{}` is not a valid Map Pool Type.'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, InvalidQuipType)):
        await SendMessage(interaction, description='`{}` is not a valid Quip Type.'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, InvalidStratRouletteTeamType)):
        await SendMessage(interaction, description='`{}` is not a valid Strat Roulette Team Type.'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, InvalidChannelType)):
        await SendMessage(interaction, description='INVALID is not a valid channel type.', color=discord.Color.red())

    elif (isinstance(error.original, InvalidRole)):
        await SendMessage(interaction, description='`@everyone` is not a valid role.', color=discord.Color.red())

    elif (isinstance(error.original, NoMMRRoles)):
        await SendMessage(interaction, description='There are no ranks.', color=discord.Color.red())

    elif (isinstance(error.original, NoQuips)):
        await SendMessage(interaction, description='There are no quips yet.', color=discord.Color.red())

    elif (isinstance(error.original, NoStratRouletteStrats)):
        await SendMessage(interaction, description='There are no Strat Roulette strats yet.', color=discord.Color.red())

    elif (isinstance(error.original, NoActivities)):
        await SendMessage(interaction, description='There are no activities yet.', color=discord.Color.red())

    elif (isinstance(error.original, PlayerAlreadyQueued)):
        await SendMessage(interaction, description='You are already in queue.', color=discord.Color.red())

    elif (isinstance(error.original, PlayerNotQueued)):
        await SendMessage(interaction, description='You are not currently in queue.', color=discord.Color.red())

    elif (isinstance(error.original, PlayerNotQueuedOrInGame)):
        await SendMessage(interaction, description='{0.mention} must be in queue or in a match.'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, PlayersNotSwapable)):
        await SendMessage(interaction, description='Player {0.mention} is not swapable with Player {1.mention}'.format(error.original.arg1, error.original.arg2), color=discord.Color.red())

    elif (isinstance(error.original, PlayerSwapFailed)):
        await SendMessage(interaction, description='Failed to find both Player {0.mention} and Player {1.mention} in the queue/start matches.'.format(error.original.arg1, error.original.arg2), color=discord.Color.red())

    elif (isinstance(error.original, InvalidCommandChannel)):
        await SendMessage(interaction, description='{0.mention} is not the correct channel for {1.value} commands.'.format(error.original.argument, error.original.type), color=discord.Color.red())

    elif (isinstance(error.original, InvalidOwnerCommandChannel)):
        await SendMessage(interaction, description='{0.mention} is not the correct channel for owner commands.'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, UserNotRegistered)):
        await SendMessage(interaction, description='User {0.mention} is not registered'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, UserAlreadyRegistered)):
        await SendMessage(interaction, description='User {0.mention} is already registered'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, MatchIDNotFound)):
        await SendMessage(interaction, description='Match with id `{}` was not found. The match history either doesn\'t exist for this match or this is not a valid match id.'.format(error.original.argument), color=discord.Color.red())

    elif (isinstance(error.original, MatchResultIdentical)):
        await SendMessage(interaction, description='The new match result is the same as the original. Nothing will happen.', color=discord.Color.red())

    elif (isinstance(error.original, UserNotAdmin)):
        await SendMessage(interaction, description='You do not have permission to run this command.', color=discord.Color.red())

    elif (isinstance(error.original, UserNotOwner)):
        await SendMessage(interaction, description='You do not have permission to run this command.', color=discord.Color.red())

    elif (isinstance(error.original, UserNotActive)):
        await SendMessage(interaction, description='You do not have permission to run this command.', color=discord.Color.red())

    elif (isinstance(error.original, EmptyName)):
        await SendMessage(interaction, description='An empty string is not a valid name.', color=discord.Color.red())

    elif (isinstance(error.original, EmptyQuip)):
        await SendMessage(interaction, description='An empty string is not a valid quip.', color=discord.Color.red())

    elif (isinstance(error.original, EmptyStrat)):
        await SendMessage(interaction, description='An empty string is not a valid Strat Roulette strat.', color=discord.Color.red())

    elif (isinstance(error.original, NoPrivateMessages)):
        await SendMessage(interaction, description='You can\'t run commands in dms.', color=discord.Color.red())

    elif (isinstance(error.original, commands.errors.MissingRequiredArgument)):
        await SendMessage(interaction, description='Invalid usage: `{0.name}` is a required argument'.format(error.original.param), color=discord.Color.red())

    elif (isinstance(error.original, commands.BadArgument)):
        await SendMessage(interaction, description='Bad Argument: {}'.format(error.original), color=discord.Color.red())

async def HandleError(ctx, error):
    print('Error: {}'.format(error))
    if (isinstance(error, commands.ChannelNotFound)):
        await SendMessage(ctx, description='`{}` is not a valid text channel.'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, commands.RoleNotFound)):
        await SendMessage(ctx, description='`{}` is not a valid role.'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, commands.UserNotFound)):
        await SendMessage(ctx, description='User not found. You can use their display name (case sensitive), id, or @ them.'.format(), color=discord.Color.red())

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

    elif (isinstance(error, InvalidActivityIndex)):
        await SendMessage(ctx, description='{0} is not a valid activity index.'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, InvalidQuipIndex)):
        await SendMessage(ctx, description='{0} is not a valid quip index.'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, InvalidStratIndex)):
        await SendMessage(ctx, description='{0} is not a valid Strat Roulette strat index.'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, InvalidGuildEmoji)):
        await SendMessage(ctx, description='{0} is not a valid guild emoji.'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, MMRRoleExists)):
        await SendMessage(ctx, description='{0.mention} is already a rank.'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, MMRRoleRangeConflict)):
        await SendMessage(ctx, description='The MMR Range you provided overlaps with another rank.', color=discord.Color.red())

    elif (isinstance(error, MapExists)):
        await SendMessage(ctx, description='`{}` is already a map'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, InvalidMap)):
        await SendMessage(ctx, description='`{}` is not a valid map.'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, MapPoolExists)):
        await SendMessage(ctx, description='`{}` is already a map pool'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, InvalidMapPool)):
        await SendMessage(ctx, description='`{}` is not a valid map pool.'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, MapPoolMapExists)):
        await SendMessage(ctx, description='`{}` is already a map in `{}`'.format(error.argument2, error.argument), color=discord.Color.red())

    elif (isinstance(error, InvalidMapPoolMap)):
        await SendMessage(ctx, description='`{}` is not a valid map in `{}`.'.format(error.argument2, error.argument), color=discord.Color.red())

    elif (isinstance(error, InvalidGuild)):
        await SendMessage(ctx, description='There is no guild set.', color=discord.Color.red())

    elif (isinstance(error, InvalidMatchResult)):
        await SendMessage(ctx, description='`{}` is not a valid Match Result.'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, InvalidActivityType)):
        await SendMessage(ctx, description='`{}` is not a valid Activity Type.'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, InvalidMapPoolType)):
        await SendMessage(ctx, description='`{}` is not a valid Map Pool Type.'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, InvalidQuipType)):
        await SendMessage(ctx, description='`{}` is not a valid Quip Type.'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, InvalidStratRouletteTeamType)):
        await SendMessage(ctx, description='`{}` is not a valid Strat Roulette Team Type.'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, NoMMRRoles)):
        await SendMessage(ctx, description='There are no ranks.', color=discord.Color.red())

    elif (isinstance(error, NoQuips)):
        await SendMessage(ctx, description='There are no quips yet.', color=discord.Color.red())

    elif (isinstance(error, NoStratRouletteStrats)):
        await SendMessage(ctx, description='There are no Strat Roulette strats yet.', color=discord.Color.red())

    elif (isinstance(error, NoActivities)):
        await SendMessage(ctx, description='There are no activities yet.', color=discord.Color.red())

    elif (isinstance(error, PlayerAlreadyQueued)):
        await SendMessage(ctx, description='You are already in queue.', color=discord.Color.red())

    elif (isinstance(error, PlayerNotQueued)):
        await SendMessage(ctx, description='You are not currently in queue.', color=discord.Color.red())

    elif (isinstance(error, PlayerNotQueuedOrInGame)):
        await SendMessage(ctx, description='{0.mention} must be in queue or in a match.'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, PlayersNotSwapable)):
        await SendMessage(ctx, description='Player {0.mention} is not swapable with Player {1.mention}'.format(error.arg1, error.arg2), color=discord.Color.red())

    elif (isinstance(error, PlayerSwapFailed)):
        await SendMessage(ctx, description='Failed to find both Player {0.mention} and Player {1.mention} in the queue/start matches.'.format(error.arg1, error.arg2), color=discord.Color.red())

    elif (isinstance(error, InvalidCommandChannel)):
        await SendMessage(ctx, description='{0.mention} is not the correct channel for {1.value} commands.'.format(error.argument, error.type), color=discord.Color.red())

    elif (isinstance(error, InvalidOwnerCommandChannel)):
        await SendMessage(ctx, description='{0.mention} is not the correct channel for owner commands.'.format(error.argument), color=discord.Color.red())

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

    elif (isinstance(error, UserNotOwner)):
        await SendMessage(ctx, description='You do not have permission to run this command.', color=discord.Color.red())

    elif (isinstance(error, UserNotActive)):
        await SendMessage(ctx, description='You do not have permission to run this command.', color=discord.Color.red())

    elif (isinstance(error, EmptyName)):
        await SendMessage(ctx, description='An empty string is not a valid name.', color=discord.Color.red())

    elif (isinstance(error, EmptyQuip)):
        await SendMessage(ctx, description='An empty string is not a valid quip.', color=discord.Color.red())

    elif (isinstance(error, EmptyStrat)):
        await SendMessage(ctx, description='An empty string is not a valid Strat Roulette strat.', color=discord.Color.red())

    elif (isinstance(error, NoPrivateMessages)):
        await SendMessage(ctx, description='You can\'t run commands in dms.', color=discord.Color.red())

    elif (isinstance(error, commands.errors.MissingRequiredArgument)):
        await SendMessage(ctx, description='Invalid usage: `{0.name}` is a required argument'.format(error.param), color=discord.Color.red())

    elif (isinstance(error, commands.BadArgument)):
        await SendMessage(ctx, description='Bad Argument: {}'.format(error), color=discord.Color.red())

