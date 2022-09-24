from pydoc import describe
from tkinter import W
from data.botsettings import ChannelTypeInvalid, GuildTextChannelMismatch, GuildRoleMismatch, InvalidChannelType, InvalidRole, RegisteredRoleUnitialized, AdminRoleUnitialized, InvalidGuild, InvalidCommandChannel, InvalidOwnerCommandChannel, UserNotAdmin, UserNotOwner, EmptyName, InvalidActivityIndex, InvalidQuipIndex, EmptyQuip, InvalidStratIndex, UserNotActive
from data.mmrrole import InvalidMMRRole, MMRRoleExists, MMRRoleRangeConflict, NoMMRRoles
from data.siegemap import CantRerollMap, MapExists, InvalidMap 
from data.playerdata import UserNotRegistered, UserAlreadyRegistered
from data.matchhistorydata import InvalidMatchResult, MatchIDNotFound, MatchResultIdentical
from data.activitydata import InvalidActivityType, NoActivities
from data.quipdata import NoQuips, InvalidQuipType, InvalidGuildEmoji
from data.mappool import CantForceMapPool, InvalidMapPool, MapPoolExists, InvalidMapPoolType, InvalidMapPoolMap, MapPoolMapExists
from data.stratroulettedata import InvalidStratRouletteTeamType, InvalidStratRouletteTeam, NoStratRouletteStrats, EmptyStrat
from services.matchservice import PlayerAlreadyQueued, PlayerNotQueued, PlayerNotQueuedOrInGame, PlayersNotSwapable, PlayerSwapFailed
from services.stratrouletteservice import StratRouletteMatchIsActive, CantStartStratRoulette, CantModifyStratRoulette
from utils.chatutils import SendMessage, SendChannelMessage

from discord.ext import commands
import discord
from discord import app_commands

class NoPrivateMessages(commands.CheckFailure):
    def __init__(self):
        super().__init__('You can\'t run commands in dms.')

async def HandleAppError(interaction:discord.Interaction, error:app_commands.AppCommandError):
    if (isinstance(error, app_commands.CheckFailure)):
        await HandleCheckFailures(interaction, error)
        return
    elif (isinstance(error, app_commands.CommandInvokeError)):
        await HandleCommandInvokeErrors(interaction, error)
        return

    print('Error: {}'.format(error))
    if (isinstance(error, RegisteredRoleUnitialized)):
        await SendErrorMessage(interaction, description='The registered role has not been setup yet.')
    elif (isinstance(error, AdminRoleUnitialized)):
        await SendErrorMessage(interaction, description='The admin role has not been setup yet.') 

async def HandleCommandInvokeErrors(interaction:discord.Interaction, error:app_commands.CommandInvokeError):
    print('Error: {}'.format(error.original))

    if (isinstance(error.original, commands.ChannelNotFound)):
        await SendErrorMessage(interaction, description='`{}` is not a valid text channel.'.format(error.original.argument))

    elif (isinstance(error.original, commands.RoleNotFound)):
        await SendErrorMessage(interaction, description='`{}` is not a valid role.'.format(error.original.argument))

    elif (isinstance(error.original, commands.UserNotFound)):
        await SendErrorMessage(interaction, description='User not found. You can use their display name (case sensitive), id, or @ them.')

    elif (isinstance(error.original, commands.MemberNotFound)):
        await SendErrorMessage(interaction, description='Member not found. You can use their display name (case sensitive), id, or @ them.')

    elif (isinstance(error.original, ChannelTypeInvalid)):
        await SendErrorMessage(interaction, description='`{}` is not a valid channel type.'.format(error.original.argument))

    elif (isinstance(error.original, GuildTextChannelMismatch)):
        await SendErrorMessage(interaction, description='`{0.mention}` is not in the same server as the other text channels'.format(error.original.argument))

    elif (isinstance(error.original, GuildRoleMismatch)):
        await SendErrorMessage(interaction, description='`{0.mention}` is not in the same server as the text channels'.format(error.original.argument))

    elif (isinstance(error.original, InvalidMMRRole)):
        await SendErrorMessage(interaction, description='{0.mention} is not a valid rank.'.format(error.original.argument))

    elif (isinstance(error.original, InvalidActivityIndex)):
        await SendErrorMessage(interaction, description='{0} is not a valid activity index.'.format(error.original.argument))

    elif (isinstance(error.original, InvalidQuipIndex)):
        await SendErrorMessage(interaction, description='{0} is not a valid quip index.'.format(error.original.argument))

    elif (isinstance(error.original, InvalidStratIndex)):
        await SendErrorMessage(interaction, description='{0} is not a valid Strat Roulette strat index.'.format(error.original.argument))

    elif (isinstance(error.original, InvalidGuildEmoji)):
        await SendErrorMessage(interaction, description='{0} is not a valid guild emoji.'.format(error.original.argument))

    elif (isinstance(error.original, MMRRoleExists)):
        await SendErrorMessage(interaction, description='{0.mention} is already a rank.'.format(error.original.argument))

    elif (isinstance(error.original, MMRRoleRangeConflict)):
        await SendErrorMessage(interaction, description='The MMR Range you provided overlaps with another rank.')

    elif (isinstance(error.original, MapExists)):
        await SendErrorMessage(interaction, description='`{}` is already a map'.format(error.original.argument))

    elif (isinstance(error.original, InvalidMap)):
        await SendErrorMessage(interaction, description='`{}` is not a valid map.'.format(error.original.argument))

    elif (isinstance(error.original, MapPoolExists)):
        await SendErrorMessage(interaction, description='`{}` is already a map pool'.format(error.original.argument))

    elif (isinstance(error.original, InvalidMapPool)):
        await SendErrorMessage(interaction, description='`{}` is not a valid map pool.'.format(error.original.argument))

    elif (isinstance(error.original, MapPoolMapExists)):
        await SendErrorMessage(interaction, description='`{}` is already a map in `{}`'.format(error.original.argument2, error.original.argument))

    elif (isinstance(error.original, InvalidMapPoolMap)):
        await SendErrorMessage(interaction, description='`{}` is not a valid map in `{}`.'.format(error.original.argument2, error.original.argument))

    elif (isinstance(error.original, CantForceMapPool)):
        await SendErrorMessage(interaction, description='You can\'t force a map pool when a match isn\'t running.')

    elif (isinstance(error.original, CantStartStratRoulette)):
        await SendErrorMessage(interaction, description='You can\'t start a Strat Roulette when a match isn\'t running.')

    elif (isinstance(error.original, CantModifyStratRoulette)):
        await SendErrorMessage(interaction, description='You can\'t modify the Strat Roulette settings when a session isn\'t running. Try starting a Strat Roulette session first!')

    elif (isinstance(error.original, CantRerollMap)):
        await SendErrorMessage(interaction, description='You can\'t reroll a map when a match isn\'t running.')

    elif (isinstance(error.original, InvalidGuild)):
        await SendErrorMessage(interaction, description='There is no guild set.')

    elif (isinstance(error.original, InvalidMatchResult)):
        await SendErrorMessage(interaction, description='`{}` is not a valid Match Result.'.format(error.original.argument))

    elif (isinstance(error.original, InvalidActivityType)):
        await SendErrorMessage(interaction, description='`{}` is not a valid Activity Type.'.format(error.original.argument))

    elif (isinstance(error.original, InvalidMapPoolType)):
        await SendErrorMessage(interaction, description='`{}` is not a valid Map Pool Type.'.format(error.original.argument))

    elif (isinstance(error.original, InvalidQuipType)):
        await SendErrorMessage(interaction, description='`{}` is not a valid Quip Type.'.format(error.original.argument))

    elif (isinstance(error.original, InvalidStratRouletteTeam)):
        await SendErrorMessage(interaction, description='`{}` is not a valid Strat Roulette Team.'.format(error.original.argument))

    elif (isinstance(error.original, InvalidStratRouletteTeamType)):
        await SendErrorMessage(interaction, description='`{}` is not a valid Strat Roulette Team Type.'.format(error.original.argument))

    elif (isinstance(error.original, InvalidChannelType)):
        await SendErrorMessage(interaction, description='INVALID is not a valid channel type.')

    elif (isinstance(error.original, InvalidRole)):
        await SendErrorMessage(interaction, description='`@everyone` is not a valid role.')

    elif (isinstance(error.original, NoMMRRoles)):
        await SendErrorMessage(interaction, description='There are no ranks.')

    elif (isinstance(error.original, NoQuips)):
        await SendErrorMessage(interaction, description='There are no quips yet.')

    elif (isinstance(error.original, NoStratRouletteStrats)):
        await SendErrorMessage(interaction, description='There are no Strat Roulette strats yet.')

    elif (isinstance(error.original, NoActivities)):
        await SendErrorMessage(interaction, description='There are no activities yet.')

    elif (isinstance(error.original, PlayerAlreadyQueued)):
        await SendErrorMessage(interaction, description='You are already in queue.')

    elif (isinstance(error.original, PlayerNotQueued)):
        await SendErrorMessage(interaction, description='You are not currently in queue.')

    elif (isinstance(error.original, PlayerNotQueuedOrInGame)):
        await SendErrorMessage(interaction, description='{0.mention} must be in queue or in a match.'.format(error.original.argument))

    elif (isinstance(error.original, PlayersNotSwapable)):
        await SendErrorMessage(interaction, description='Player {0.mention} is not swapable with Player {1.mention}'.format(error.original.arg1, error.original.arg2))

    elif (isinstance(error.original, PlayerSwapFailed)):
        await SendErrorMessage(interaction, description='Failed to find both Player {0.mention} and Player {1.mention} in the queue/start matches.'.format(error.original.arg1, error.original.arg2)) 

    elif (isinstance(error.original, MatchIDNotFound)):
        await SendErrorMessage(interaction, description='Match with id `{}` was not found. The match history either doesn\'t exist for this match or this is not a valid match id.'.format(error.original.argument))

    elif (isinstance(error.original, MatchResultIdentical)):
        await SendErrorMessage(interaction, description='The new match result is the same as the original. Nothing will happen.')

    elif (isinstance(error.original, EmptyName)):
        await SendErrorMessage(interaction, description='An empty string is not a valid name.')

    elif (isinstance(error.original, EmptyQuip)):
        await SendErrorMessage(interaction, description='An empty string is not a valid quip.')

    elif (isinstance(error.original, EmptyStrat)):
        await SendErrorMessage(interaction, description='An empty string is not a valid Strat Roulette strat.')

    elif (isinstance(error.original, StratRouletteMatchIsActive)):
        await SendErrorMessage(interaction, description='There is already an active strat roulette match. Please finish it first before starting a new one.')

    elif (isinstance(error.original, commands.errors.MissingRequiredArgument)):
        await SendErrorMessage(interaction, description='Invalid usage: `{0.name}` is a required argument'.format(error.original.param))

    elif (isinstance(error.original, commands.BadArgument)):
        await SendErrorMessage(interaction, description='Bad Argument: {}'.format(error.original))

async def HandleCheckFailures(interaction:discord.Interaction, error:app_commands.CheckFailure):
    print('Error: {}'.format(error))

    if (isinstance(error, InvalidCommandChannel)):
        await SendErrorMessage(interaction, description='{0.mention} is not the correct channel for {1.value} commands.'.format(error.argument, error.type))
    elif (isinstance(error, UserNotRegistered)):
        await SendErrorMessage(interaction, description='User {0.mention} is not registered'.format(error.argument))
    elif (isinstance(error, UserAlreadyRegistered)):
        await SendErrorMessage(interaction, description='User {0.mention} is already registered'.format(error.argument))
    elif (isinstance(error, NoPrivateMessages)):
        await SendErrorMessage(interaction, description='You can\'t run commands in dms.')
    # Default
    # UserNotAdmin
    # UserNotActive
    else:
        await SendErrorMessage(interaction, description='You do not have permission to run this command.')

async def SendErrorMessage(interaction:discord.Interaction, **kwargs):
    await SendMessage(interaction, color=discord.Color.red(), ephemeral=True, **kwargs)

async def SendOldErrorMessage(ctx, **kwargs):
    await SendChannelMessage(ctx.channel, color=discord.Color.red(), **kwargs)

async def HandleError(ctx, error):
    print('Error: {}'.format(error))
    if (isinstance(error, commands.ChannelNotFound)):
        await SendOldErrorMessage(ctx, description='`{}` is not a valid text channel.'.format(error.argument))

    elif (isinstance(error, commands.RoleNotFound)):
        await SendOldErrorMessage(ctx, description='`{}` is not a valid role.'.format(error.argument))

    elif (isinstance(error, commands.UserNotFound)):
        await SendOldErrorMessage(ctx, description='User not found. You can use their display name (case sensitive), id, or @ them.'.format())

    elif (isinstance(error, commands.MemberNotFound)):
        await SendOldErrorMessage(ctx, description='Member not found. You can use their display name (case sensitive), id, or @ them.'.format())

    elif (isinstance(error, InvalidOwnerCommandChannel) or isinstance(error, UserNotOwner)):
        commandName = ctx.command.name
        await SendOldErrorMessage(ctx, description='`{}` is not a valid command. Have you tried looking at slash commands? Type / and see what is available!'.format(commandName))

    elif (isinstance(error, commands.CommandNotFound)):
        commandName = '{}'.format(error)
        startIndex = commandName.find('"')
        endIndex = commandName.find('"', startIndex + 1)
        commandName = commandName[startIndex + 1:endIndex]
        await SendOldErrorMessage(ctx, description='`{}` is not a valid command. Have you tried looking at slash commands? Type / and see what is available!'.format(commandName))

    elif (isinstance(error, InvalidQuipIndex)):
        await SendOldErrorMessage(ctx, description='{0} is not a valid quip index.'.format(error.argument))

    elif (isinstance(error, InvalidGuildEmoji)):
        await SendOldErrorMessage(ctx, description='{0} is not a valid guild emoji.'.format(error.argument))

    elif (isinstance(error, InvalidGuild)):
        await SendOldErrorMessage(ctx, description='There is no guild set.')

    elif (isinstance(error, InvalidQuipType)):
        await SendOldErrorMessage(ctx, description='`{}` is not a valid Quip Type.'.format(error.argument))

    elif (isinstance(error, InvalidActivityIndex)):
        await SendOldErrorMessage(ctx, description='{0} is not a valid activity index.'.format(error.argument))

    elif (isinstance(error, InvalidActivityType)):
        await SendOldErrorMessage(ctx, description='`{}` is not a valid Activity Type.'.format(error.argument))
        
    elif (isinstance(error, NoQuips)):
        await SendOldErrorMessage(ctx, description='There are no quips yet.')

    elif (isinstance(error, NoActivities)):
        await SendOldErrorMessage(ctx, description='There are no activities yet.')

    elif (isinstance(error, EmptyQuip)):
        await SendOldErrorMessage(ctx, description='An empty string is not a valid quip.')

    elif (isinstance(error, EmptyName)):
        await SendOldErrorMessage(ctx, description='An empty string is not a valid name.')

    elif (isinstance(error, NoPrivateMessages)):
        await SendOldErrorMessage(ctx, description='You can\'t run commands in dms.')

    elif (isinstance(error, commands.errors.MissingRequiredArgument)):
        await SendOldErrorMessage(ctx, description='Invalid usage: `{0.name}` is a required argument'.format(error.param))

    elif (isinstance(error, commands.BadArgument)):
        await SendOldErrorMessage(ctx, description='Bad Argument: {}'.format(error))

