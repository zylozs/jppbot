from pydoc import describe
from discord.ext import commands
from data.botsettings import ChannelType, GuildTextChannelMismatch, GuildRoleMismatch, InvalidChannelType , InvalidGuild, InvalidRole, RegisteredRoleUnitialized, EmptyName, InvalidStratIndex
from data.playerdata import UserNotRegistered, UserAlreadyRegistered
from data.matchhistorydata import MatchHistoryData, InvalidMatchResult, MatchIDNotFound, MatchResultIdentical, MatchResult
from data.mmrrole import MMRRoleExists, MMRRoleRangeConflict, InvalidMMRRole, NoMMRRoles
from data.siegemap import MapExists, InvalidMap, CantRerollMap
from data.mappool import CantForceMapPool, MapPoolExists, InvalidMapPool, MapPoolType, InvalidMapPoolType, InvalidMapPoolMap, MapPoolMapExists
from data.stratroulettedata import StratRouletteData, StratRouletteTeamType, NoStratRouletteStrats
from services.matchservice import TeamResult, PlayerNotQueuedOrInGame, PlayersNotSwapable
from utils.botutils import IsAdmin, IsValidChannel, AddRoles, RemoveRoles, GuildCommand
from utils.errorutils import HandleAppError, HandleError
from utils.chatutils import SendMessage, SendChannelMessage, SendMessageEdit
from globals import *
from mongoengine import disconnect
from discord import app_commands
from discord.app_commands import Choice
import discord
import math
import random

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @GuildCommand(name='quit')
    @IsAdmin()
    async def OnQuit(self, interaction:discord.Interaction):
        """Shuts down the bot"""
        goodbye = ['au revoir', 'goodbye', 'cya', 'à la prochaine']
        await interaction.response.send_message(random.choice(goodbye))
        print('User {} has requested a quit. Closing bot.'.format(interaction.user))
        disconnect() # disconect our MongoDB instance
        await self.bot.close() # close our bot instance

    @GuildCommand(name='forceregister')
    @IsAdmin()
    @app_commands.describe(member='The member you want to register.', mmr='The initial MMR you want to give the member.')
    async def OnForceRegisterPlayer(self, interaction:discord.Interaction, member:discord.Member, mmr:int):
        """Registers a player
        
           **discord.Member:** <member>
           The member you want to register.
           You can use any of the following to identify them:
           - ID (i.e. 123456789)
           - mention (i.e. @Name)
           - name#discrim (i.e. Name#1234  (case sensitive))
           - name (i.e. Name  (case sensitive)
           - nickname (i.e. Nickname  (case sensitive))

           **int:** <initialMMR>
           The initial MMR you want to give the user with the bot.
        """
        name = '{}'.format(member.name)
        print('User {0.user} is force registering {1} with name {2} and initial mmr of {3}'.format(interaction, member, name, mmr))

        if (botSettings.registeredRole is None):
            raise RegisteredRoleUnitialized()

        if (botSettings.IsUserRegistered(member)):
            raise UserAlreadyRegistered(member)

        try:
            await member.add_roles(botSettings.registeredRole, reason='User {0.name} used the forceregister command'.format(interaction.user))

            botSettings.RegisterUser(member, name)

            botSettings.SetMMR(member, mmr)

            await SendMessage(interaction, description='You have registered {0.mention} as `{1}` with an initial MMR of {2}.'.format(member, name, mmr), color=discord.Color.blue())
        except discord.HTTPException:
            await SendMessage(interaction, description='Registration failed. Please try again.', color=discord.Color.red())

    @GuildCommand(name='clearqueue')
    @IsAdmin()
    async def OnClearQueue(self, interaction:discord.Interaction):
        """Clears the matchmaking queue"""
        print('Clearing queue')

        await matchService.ClearQueue(interaction)

    @GuildCommand(name='kick')
    @IsAdmin()
    @app_commands.describe(member='The member you want to kick.')
    async def OnKickPlayerFromQueue(self, interaction:discord.Interaction, member:discord.Member):
        """Kicks a player from the matchmaking queue
        
           **discord.Member:** <member>
           The member you want to kick. 
           You can use any of the following to identify them:
           - ID (i.e. 123456789)
           - mention (i.e. @Name)
           - name#discrim (i.e. Name#1234  (case sensitive))
           - name (i.e. Name  (case sensitive)
           - nickname (i.e. Nickname  (case sensitive))
        """
        print('{} is kicking {} from the queue'.format(interaction.user, member))

        await matchService.KickFromQueue(interaction, member)

    @GuildCommand(name='forcestartmatch')
    @IsAdmin()
    @app_commands.rename(fill_with_fake_players='debug')
    @app_commands.describe(fill_with_fake_players='DEBUG ONLY: Fills the lobby with fake players.')
    async def OnForceStartMatch(self, interaction:discord.Interaction, fill_with_fake_players:bool = False):
        """Starts the match
        
           **bool:** <fill_with_fake_players>
           Fills the lobby with fake players. This is useful for testing bot functionality without having 10 players. **DO NOT USE IN A REAL MATCH**
        """
        print('{} is force starting the match {}'.format(interaction.user, 'and filling with fake users' if fill_with_fake_players else ''))

        await SendMessage(interaction, description='{0.mention} is force starting the match!'.format(interaction.user), color=discord.Color.blue())
        await matchService.StartMatch(fill_with_fake_players)

    @GuildCommand(name='clearchannel')
    @IsAdmin()
    @app_commands.describe(channel_type='The channel type to clear from the bot\'s settings.')
    @app_commands.choices(channel_type=[
        Choice(name='Admin', value=ChannelType.ADMIN.value),
        Choice(name='Lobby', value=ChannelType.LOBBY.value),
        Choice(name='Register', value=ChannelType.REGISTER.value),
        Choice(name='Report', value=ChannelType.REPORT.value),
        Choice(name='Results', value=ChannelType.RESULTS.value) ])
    async def OnClearChannel(self, interaction:discord.Interaction, channel_type:Choice[str]):
        """Clears a channel from use with the bot

           **string:** <channel_type>
           Types available (not case sensitive):
           - lobby
           - register
           - results
           - report
           - admin
        """
        print('Channel type: {}'.format(channel_type.value))

        type = await ChannelType.convert(channel_type.value)

        if (type == ChannelType.INVALID):
            raise InvalidChannelType()

        if (type is ChannelType.LOBBY):
            channel = botSettings.lobbyChannel
            botSettings.SetLobbyChannel(None)
        elif (type is ChannelType.REGISTER):
            channel = botSettings.registerChannel
            botSettings.SetRegisterChannel(None)
        elif (type is ChannelType.ADMIN):
            channel = botSettings.adminChannel
            botSettings.SetAdminChannel(None)
        elif (type is ChannelType.RESULTS):
            channel = botSettings.resultsChannel
            botSettings.SetResultsChannel(None)
        elif (type is ChannelType.REPORT):
            channel = botSettings.reportChannel
            botSettings.SetReportChannel(None)

        await SendMessage(interaction, description='{0.mention} has been cleared as the {1.value} channel'.format(channel, type), color=discord.Color.blue())

    @GuildCommand(name='setchannel')
    @IsAdmin()
    @app_commands.describe(channel='The text channel you want to use for the channel type.', channel_type='The channel type to associate with the text channel.')
    @app_commands.choices(channel_type=[
        Choice(name='Admin', value=ChannelType.ADMIN.value),
        Choice(name='Lobby', value=ChannelType.LOBBY.value),
        Choice(name='Register', value=ChannelType.REGISTER.value),
        Choice(name='Report', value=ChannelType.REPORT.value),
        Choice(name='Results', value=ChannelType.RESULTS.value) ])
    async def OnSetChannel(self, interaction:discord.Interaction, channel:discord.TextChannel, channel_type:Choice[str]):
        """Sets a channel for use with the bot

           **discord.TextChannel:** <channel>
           The text channel you want to use.
           You can use any of the following to identify it:
           - ID (i.e. 123456789)
           - mention (i.e. #Name)
           - name (i.e. Name  (case sensitive)

           **string:** <channel_type>
           Types available (not case sensitive):
           - lobby
           - register
           - results
           - report
           - admin
        """
        print('Setting Channel: {} type: {}'.format(channel, channel_type.value))

        type = await ChannelType.convert(channel_type.value)

        # setup guild if missing
        if (botSettings.guild is None):
            botSettings.SetGuild(channel.guild)
        elif (botSettings.guild is not channel.guild):
            raise GuildTextChannelMismatch(channel)

        if (type is ChannelType.INVALID):
            raise InvalidChannelType()

        if (type is ChannelType.LOBBY):
            botSettings.SetLobbyChannel(channel)
        elif (type is ChannelType.REGISTER):
            botSettings.SetRegisterChannel(channel)
        elif (type is ChannelType.ADMIN):
            botSettings.SetAdminChannel(channel)
        elif (type is ChannelType.RESULTS):
            botSettings.SetResultsChannel(channel)
        elif (type is ChannelType.REPORT):
            botSettings.SetReportChannel(channel)

        await SendMessage(interaction, description='{0.mention} has been set as the {1.value} channel'.format(channel, type), color=discord.Color.blue())

    @GuildCommand(name='channels')
    @IsAdmin()
    async def OnShowChannels(self, interaction:discord.Interaction):
        """Shows the channels used by the bot"""
        print('Showing channels')

        description='Lobby Channel: {}\n'.format('Not setup' if botSettings.lobbyChannel is None else botSettings.lobbyChannel.mention)
        description+='Register Channel: {}\n'.format('Not setup' if botSettings.registerChannel is None else botSettings.registerChannel.mention)
        description+='Report Channel: {}\n'.format('Not setup' if botSettings.reportChannel is None else botSettings.reportChannel.mention)
        description+='Results Channel: {}\n'.format('Not setup' if botSettings.resultsChannel is None else botSettings.resultsChannel.mention)
        description+='Admin Channel: {}'.format('Not setup' if botSettings.adminChannel is None else botSettings.adminChannel.mention)

        await SendMessage(interaction, description=description, color=discord.Color.blue())

    @GuildCommand(name='setregisteredrole')
    @IsAdmin()
    @app_commands.describe(role='The role you want to use for registered players.')
    async def OnSetRegisteredRole(self, interaction:discord.Interaction, role:discord.Role):
        """Sets the registered role

           **discord.Role:** <role>
           The role you want to use for registered players.
           You can use any of the following to identify it:
           - ID (i.e. 123456789)
           - mention (i.e. @RoleName)
           - name (i.e. RoleName  (case sensitive)
        """
        print('Setting Registered Role: {}'.format(role))

        if (role.name == '@everyone' or role.name == '@here'):
            raise InvalidRole(role)

        # setup guild if missing
        if (botSettings.guild is None):
            botSettings.SetGuild(role.guild)
        elif (botSettings.guild is not role.guild):
            raise GuildRoleMismatch(role)

        if (botSettings.registeredRole is not None):
            title = 'Warning: You are changing the registered role.'
            description = 'This will not affect players who are already registered. The previous role {0.mention} will not be automatically changed on registered players, however the role is purely cosmetic.'.format(botSettings.registeredRole)
            await SendChannelMessage(interaction.channel, title=title, description=description, color=discord.Color.gold())

        botSettings.SetRegisteredRole(role)
        await SendMessage(interaction, description='The registered role has been updated.', color=discord.Color.blue())

    @GuildCommand(name='setadminrole')
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(role='The role you want to use to give admin priviledges with the bot.')
    async def OnSetAdminRole(self, interaction:discord.Interaction, role:discord.Role):
        """Sets the admin role

           **discord.Role:** <role>
           The role you want to use to give admin priviledges with the bot.
           You can use any of the following to identify it:
           - ID (i.e. 123456789)
           - mention (i.e. @RoleName)
           - name (i.e. RoleName  (case sensitive)
        """
        print('Setting Admin Role: {}'.format(role))

        if (role.name == '@everyone' or role.name == '@here'):
            raise InvalidRole(role)

        # setup guild if missing
        if (botSettings.guild is None):
            botSettings.SetGuild(role.guild)
        elif (botSettings.guild is not role.guild):
            raise GuildRoleMismatch(role)

        if (botSettings.adminRole is not None):
            title = 'Warning: You are changing the admin role.'
            description = 'This may impact members with the previous admin role {0.mention}. They will need their role updated to regain admin priviledges with the bot.'.format(botSettings.adminRole)
            await SendChannelMessage(interaction.channel, title=title, description=description, color=discord.Color.gold())

        botSettings.SetAdminRole(role)
        await SendMessage(interaction, description='The admin role has been updated.', color=discord.Color.blue())

    @GuildCommand(name='addrank')
    @IsAdmin()
    @app_commands.describe(role='The role you want to use for a rank.', 
        mmr_min='The minimum MMR for this rank (inclusive).', 
        mmr_max='The maximum MMR for this rank (inclusive).', 
        mmr_delta='The MMR increase or decrease after each match.')
    async def OnAddRank(self, interaction:discord.Interaction, role:discord.Role, mmr_min:int, mmr_max:int, mmr_delta:int):
        """Adds a rank

           **discord.Role:** <role>
           The role you want to use for a rank.
           You can use any of the following to identify it:
           - ID (i.e. 123456789)
           - mention (i.e. @RoleName)
           - name (i.e. RoleName  (case sensitive)

           **int:** <mmr_min>
           The minimum MMR for this rank (inclusive)

           **int:** <mmr_max>
           The maximum MMR for this rank (inclusive)

           **int:** <mmr_delta>
           The MMR increase or decrease after each match
        """
        print('Adding new rank: {} min: {} max: {} delta: {}'.format(role, mmr_min, mmr_max, mmr_delta))

        if (role.name == '@everyone' or role.name == '@here'):
            raise InvalidRole()

        # setup guild if missing
        if (botSettings.guild is None):
            botSettings.SetGuild(role.guild)
        elif (botSettings.guild is not role.guild):
            raise GuildRoleMismatch(role)

        if (botSettings.IsValidMMRRole(role)):
            raise MMRRoleExists(role)

        if (not botSettings.IsMMRRoleRangeValid(mmr_min, mmr_max)):
            raise MMRRoleRangeConflict()

        botSettings.AddMMRRole(role, mmr_min, mmr_max, mmr_delta)
        await SendMessage(interaction, title='New Rank Added', description='Role: {0.mention}\nMMR Range: {1}-{2}\nMMR Delta: +-{3}'.format(role, mmr_min, mmr_max, mmr_delta), color=discord.Color.blue())

    @GuildCommand(name='updaterank')
    @IsAdmin()
    @app_commands.describe(role='The role associated with the rank you want to update.',
        mmr_min='The minimum MMR for this rank (inclusive).', 
        mmr_max='The maximum MMR for this rank (inclusive).', 
        mmr_delta='The MMR increase or decrease after each match.')
    async def OnUpdateRank(self, interaction:discord.Interaction, role:discord.Role, mmr_min:int, mmr_max:int, mmr_delta:int):
        """Updates a rank's mmr range and delta

           **discord.Role:** <role>
           The role associated with the rank you want to update
           You can use any of the following to identify it:
           - ID (i.e. 123456789)
           - mention (i.e. @RoleName)
           - name (i.e. RoleName  (case sensitive)

           **int:** <mmr_min>
           The minimum MMR for this rank (inclusive)

           **int:** <mmr_max>
           The maximum MMR for this rank (inclusive)

           **int:** <mmr_delta>
           The MMR increase or decrease after each match
        """
        print('Updating existing rank: {} min: {} max: {} delta: {}'.format(role, mmr_min, mmr_max, mmr_delta))

        if (role.name == '@everyone' or role.name == '@here'):
            raise InvalidRole()

        # setup guild if missing
        if (botSettings.guild is None):
            botSettings.SetGuild(role.guild)
        elif (botSettings.guild is not role.guild):
            raise GuildRoleMismatch(role)

        if (not botSettings.IsValidMMRRole(role)):
            raise InvalidMMRRole(role)

        if (not botSettings.IsMMRRoleRangeValid(mmr_min, mmr_max)):
            raise MMRRoleRangeConflict()

        botSettings.UpdateMMRRole(role, mmr_min, mmr_max, mmr_delta)
        await SendMessage(interaction, title='Rank Updated', description='Role: {0.mention}\nMMR Range: {1}-{2}\nMMR Delta: +-{3}'.format(role, mmr_min, mmr_max, mmr_delta), color=discord.Color.blue())

    @GuildCommand(name='removerank')
    @IsAdmin()
    @app_commands.describe(role='The role associated with the rank you want to remove.')
    async def OnRemoveRank(self, interaction:discord.Interaction, role:discord.Role):
        """Removes a rank

           **discord.Role:** <role>
           The role associated with the rank you want to remove 
           You can use any of the following to identify it:
           - ID (i.e. 123456789)
           - mention (i.e. @RoleName)
           - name (i.e. RoleName  (case sensitive)
        """
        print('Removing rank: {}'.format(role))

        if (role.name == '@everyone' or role.name == '@here'):
            raise InvalidRole()

        # setup guild if missing
        if (botSettings.guild is None):
            botSettings.SetGuild(role.guild)
        elif (botSettings.guild is not role.guild):
            raise GuildRoleMismatch(role)

        if (not botSettings.IsValidMMRRole(role)):
            raise InvalidMMRRole(role)

        mmrMin = botSettings.mmrRoles[role.id].mmrMin
        mmrMax = botSettings.mmrRoles[role.id].mmrMax
        mmrDelta = botSettings.mmrRoles[role.id].mmrDelta

        for player in botSettings.registeredPlayers.values():
            if player.user is None:
                continue

            member = botSettings.guild.get_member(player.user.id)
            if member is not None and role in member.roles:
                await RemoveRoles(interaction, member, role, errorMessage='Failed to remove rank. Please try again.')

        botSettings.RemoveMMRRole(role)
        await SendMessage(interaction, title='Rank Removed', description='Role: {0.mention}\nMMR Range: {1}-{2}\nMMR Delta: +-{3}'.format(role, mmrMin, mmrMax, mmrDelta), color=discord.Color.blue())

    @GuildCommand(name='setmmr')
    @IsAdmin()
    @app_commands.describe(member='The member you want to change the mmr of.', mmr='The mmr you want to set the member to.')
    async def OnSetMMR(self, interaction:discord.Interaction, member:discord.Member, mmr:int):
        """Set a player's mmr

           **discord.Member:** <member>
           The member you want to change the mmr of. 
           You can use any of the following to identify them:
           - ID (i.e. 123456789)
           - mention (i.e. @Name)
           - name#discrim (i.e. Name#1234  (case sensitive))
           - name (i.e. Name  (case sensitive)
           - nickname (i.e. Nickname  (case sensitive))

           **int:** <mmr>
           The mmr you want to set the member to.
        """
        print('Setting MMR on {0} to {1}'.format(member, mmr))

        if (not botSettings.IsUserRegistered(member)):
            raise UserNotRegistered(member)

        previousMMR = botSettings.SetMMR(member, mmr)

        previousRole, newRole = botSettings.GetMMRRole(member, previousMMR)

        if (previousRole is not None):
            await RemoveRoles(interaction, member, previousRole.role, errorMessage='Failed to remove previous rank. Please try again.')
        
        if (newRole is not None):
            await AddRoles(interaction, member, newRole.role, errorMessage='Failed to add new rank. Please try again.')

        field = {}
        field['name'] = 'MMR Updated'
        field['value'] = 'Player: {0.mention}:\nMMR: {1} -> {2}'.format(member, previousMMR, mmr)
        field['inline'] = False

        if (previousRole is None and newRole is not None):
            field['value'] += '\nRank: {0.mention}'.format(newRole.role)
        elif (previousRole is not None and newRole is not None):
            field['value'] += '\nRank: {0.mention} -> {1.mention}'.format(previousRole.role, newRole.role)

        matchService.UpdateMMR(member, mmr)

        await SendMessage(interaction, fields=[field], color=discord.Color.blue())

    @GuildCommand(name='refreshuser')
    @IsAdmin()
    @app_commands.describe(member='The member you want to refresh roles on.')
    async def OnRefreshUser(self, interaction:discord.Interaction, member:discord.Member):
        """Refresh a user's roles
        
           **discord.Member:** <member>
           The member you want to refresh roles on.
           You can use any of the following to identify them:
           - ID (i.e. 123456789)
           - mention (i.e. @Name)
           - name#discrim (i.e. Name#1234  (case sensitive))
           - name (i.e. Name  (case sensitive)
           - nickname (i.e. Nickname  (case sensitive))
        """
        print('Refreshing roles for user {}'.format(member))

        if (botSettings.guild is None):
            raise InvalidGuild()

        if (not botSettings.IsUserRegistered(member)):
            raise UserNotRegistered(member)

        mmrRoles = botSettings.GetAllMMRRoles()

        if (len(mmrRoles) == 0):
            raise NoMMRRoles()

        previousRole, newRole = botSettings.GetMMRRole(member)

        # Remove all their previous mmr roles and readd the correct one
        await RemoveRoles(interaction, member, *mmrRoles, errorMessage='Failed to remove previous rank from {0.mention}. Please try again.'.format(member))
        await AddRoles(interaction, member, newRole.role, botSettings.registeredRole, errorMessage='Failed to add current rank to {0.mention}. Please try again.'.format(member))
    
        await SendMessage(interaction, description='Ranks have been updated on {0.mention}'.format(member), color=discord.Color.blue())

    @GuildCommand(name='refreshusers')
    @IsAdmin()
    async def OnRefreshUsers(self, interaction:discord.Interaction):
        """Refresh all user roles"""
        print('Refreshing roles on all users')

        if (botSettings.guild is None):
            raise InvalidGuild()

        mmrRoles = botSettings.GetAllMMRRoles()

        if (len(mmrRoles) == 0):
            raise NoMMRRoles()

        # Acknowledge the request immediately since it can take a lot of time to perform the action
        await interaction.response.defer(thinking=True)

        for player in botSettings.registeredPlayers.values():
            if player.user is None:
                continue

            previousRole, newRole = botSettings.GetMMRRole(player.user)

            member = botSettings.guild.get_member(player.user.id)

            # Just ignore users who aren't in the guild
            if (member is None):
                continue

            # Remove all their previous mmr roles and readd the correct one
            await RemoveRoles(interaction, member, *mmrRoles, errorMessage='Failed to remove previous rank from {0.mention}. Please try again.'.format(member))
            await AddRoles(interaction, member, newRole.role, botSettings.registeredRole, errorMessage='Failed to add current rank to {0.mention}. Please try again.'.format(member))

        await SendMessageEdit(interaction, description='Ranks have been updated on all registered players.', color=discord.Color.blue())

    @GuildCommand(name='addmap')
    @IsAdmin()
    @app_commands.describe(name='The name of the map you want to add. Casing is preserved.', thumbnail_url='The url of hte image you want to use as the map\'s thumbnail.')
    async def OnAddMap(self, interaction:discord.Interaction, name:str, thumbnail_url:str =''):
        """Adds a map

           **string:** <name>
           The name of the map you want to add. Casing is preserved, but name validation is not case sensitive.

           **string:** <thumbnailURL> (Optional)
           **Default value:** ''
           The url of the image you want to use as the map's thumbnail. Omit if you dont want a thumbnail.
        """
        print('Adding map {} with thumbnail {}'.format(name, thumbnail_url))

        if (botSettings.DoesMapExist(name)):
            raise MapExists(name)

        botSettings.AddMap(name, thumbnail_url)
        await SendMessage(interaction, description='`{}` has been added as a map.'.format(name), color=discord.Color.blue())

    @GuildCommand(name='removemap')
    @IsAdmin()
    @app_commands.describe(name='The name of the map you want to remove. This is not case sensitive.')
    async def OnRemoveMap(self, interaction:discord.Interaction, name:str):
        """Removes a map
        
           **string:** <name>
           The name of the map you want to remove. This is not case sensitive.
        """
        print('Removing map: {}'.format(name))

        if (not botSettings.DoesMapExist(name)):
            raise InvalidMap(name)

        botSettings.RemoveMap(name)
        await SendMessage(interaction, description='`{}` has been removed as a map.'.format(name), color=discord.Color.blue())	

    @GuildCommand(name='setmapthumbnail')
    @IsAdmin()
    @app_commands.describe(name='The name of the map you want to add. This is not case sensitive.', thumbnail_url='The url of the image you want to use as the map\'s thumbnail.')
    async def OnSetMapThumbnail(self, interaction:discord.Interaction, name:str, thumbnail_url:str):
        """Changes the thumbnail for a map

           **string:** <name>
           The name of the map you want to add. This is not case sensitive. 

           **string:** <thumbnailURL>
           The url of the image you want to use as the map's thumbnail. 
        """
        print('Setting thumbnail for map {} to {}'.format(name, thumbnail_url))

        if (not botSettings.DoesMapExist(name)):
            raise InvalidMap(name)

        botSettings.SetMapThumbnail(name, thumbnail_url)
        await SendMessage(interaction, description='`{}` has been set as the thumbnail for map {}.'.format(thumbnail_url, name), color=discord.Color.blue())	

    @GuildCommand(name='addpool')
    @IsAdmin()
    @app_commands.describe(name='The name of the map pool you want to add. Casing is preserved.', pool_type='The type of Map Pool you want to have.')
    @app_commands.choices(pool_type=[
        Choice(name='All', value=MapPoolType.ALL.value),
        Choice(name='Custom', value=MapPoolType.CUSTOM.value),
        Choice(name='Exclude', value=MapPoolType.EXCLUDE.value) ])
    async def OnAddMapPool(self, interaction:discord.Interaction, name:str, pool_type:Choice[int]):
        """Adds a map pool

           **string:** <name>
           The name of the map pool you want to add. Casing is preserved, but name validation is not case sensitive.

           **string|int:** <type>
           The type of Map Pool you want to have.
           Available results (not case sensitive):
           - 0 (All maps)
           - 1 (Custom map list)
           - 2 (All maps excluding specified)
           - all (All maps)
           - a (All maps)
           - custom (Custom map list)
           - c (Custom map list)
           - exclude (All maps excluding specified)
           - e (All maps excluding specified)
        """

        type = await MapPoolType.convert(pool_type.value)

        if (type == MapPoolType.INVALID):
            raise InvalidMapPoolType(type)

        if (botSettings.DoesMapPoolExist(name)):
            raise MapPoolExists(name)

        botSettings.AddMapPool(name, type.value)
        await SendMessage(interaction, description='`{}` has been added as a map pool.'.format(name), color=discord.Color.blue())

    @GuildCommand(name='removepool')
    @IsAdmin()
    @app_commands.describe(name='The name of the map pool you want to remove. This is not case sensitive.')
    async def OnRemoveMapPool(self, interaction:discord.Interaction, name:str):
        """Removes a map pool
        
           **string:** <name>
           The name of the map pool you want to remove. This is not case sensitive. 
        """

        if (not botSettings.DoesMapPoolExist(name)):
            raise InvalidMapPool(name)

        botSettings.RemoveMapPool(name)
        await SendMessage(interaction, description='`{}` has been removed as a map pool.'.format(name), color=discord.Color.blue())

    @GuildCommand(name='setpooltype')
    @IsAdmin()
    @app_commands.describe(name='The name of the map pool you want to modify. This is not case sensitive.', pool_type='The type of Map Pool you want to have.')
    @app_commands.choices(pool_type=[
        Choice(name='All', value=MapPoolType.ALL.value),
        Choice(name='Custom', value=MapPoolType.CUSTOM.value),
        Choice(name='Exclude', value=MapPoolType.EXCLUDE.value) ])
    async def OnSetMapPoolType(self, interaction:discord.Interaction, name:str, pool_type:Choice[int]):
        """Sets an existing map pool's type

           **string:** <name>
           The name of the map pool you want to modify. This is not case sensitive.

           **string|int:** <type>
           The type of Map Pool you want to have.
           Available results (not case sensitive):
           - 0 (All maps)
           - 1 (Custom map list)
           - 2 (All maps excluding specified)
           - all (All maps)
           - a (All maps)
           - custom (Custom map list)
           - c (Custom map list)
           - exclude (All maps excluding specified)
           - e (All maps excluding specified)
        """
        type = await MapPoolType.convert(pool_type.value)

        if (type == MapPoolType.INVALID):
            raise InvalidMapPoolType(type)

        if (not botSettings.DoesMapPoolExist(name)):
            raise InvalidMapPool(name)

        botSettings.pools[name.lower()].SetType(type.value)
        await SendMessage(interaction, description='`{}` has changed Map Pool type to `{}`'.format(name, type.name), color=discord.Color.blue())

    @GuildCommand(name='addpoolmap')
    @IsAdmin()
    @app_commands.describe(pool_name='The name of the map pool you want to add it to. This is not case sensitive.', map_name='The name of the map you want to add. This is not case sensitive.')
    async def OnAddMapPoolMap(self, interaction:discord.Interaction, pool_name:str, map_name:str):
        """Adds a map to a map pool

           **string:** <pool_name>
           The name of the map pool you want to add it to. This is not case sensitive. 

           **string:** <map_name>
           The name of the map you want to add. This is not case sensitive.
        """

        if (not botSettings.DoesMapExist(map_name)):
            raise InvalidMap(map_name)

        mapProperName = botSettings.GetMapProperName(map_name)

        if (not botSettings.DoesMapPoolExist(pool_name)):
            raise InvalidMapPool(pool_name)

        if (botSettings.DoesMapPoolMapExist(pool_name, mapProperName)):
            raise MapPoolMapExists(pool_name, mapProperName)

        botSettings.AddMapPoolMap(pool_name, mapProperName)
        await SendMessage(interaction, description='`{}` has been added to map pool `{}`.'.format(mapProperName, pool_name), color=discord.Color.blue())

    @GuildCommand(name='removepoolmap')
    @IsAdmin()
    @app_commands.describe(pool_name='The name of the map pool you want to remove it from. This is not case sensitive.', map_name='The name of the map you want to remove. This is not case sensitive.')
    async def OnRemoveMapPoolMap(self, interaction:discord.Interaction, pool_name:str, map_name:str):
        """Removes a map from a map pool

           **string:** <pool_name>
           The name of the map pool you want to remove it from. This is not case sensitive. 

           **string:** <map_name>
           The name of the map you want to remove. This is not case sensitive. 
        """
        if (not botSettings.DoesMapExist(map_name)):
            raise InvalidMap(map_name)

        mapProperName = botSettings.GetMapProperName(map_name)

        if (not botSettings.DoesMapPoolExist(pool_name)):
            raise InvalidMapPool(pool_name)

        if (not botSettings.DoesMapPoolMapExist(pool_name, mapProperName)):
            raise InvalidMapPoolMap(pool_name, mapProperName)

        botSettings.RemoveMapPoolMap(pool_name, mapProperName)
        await SendMessage(interaction, description='`{}` has been removed from map pool `{}`.'.format(mapProperName, pool_name), color=discord.Color.blue())
    
    @GuildCommand(name='leaderboard')
    @IsAdmin()
    @app_commands.describe(page='The page of the leaderboards you want to show.', broadcast='Whether or not to broadcast the leaderboards for everyone to see.')
    async def OnShowLeaderboards(self, interaction:discord.Interaction, page:int=1, broadcast:bool=True):
        """Shows the leaderboards
        
           **int:** <page>
           **Default value:** 1
           The page of the leaderboards you want to show.

           **bool:** <broadcast>
           **Default value:** True
           Whether or not to broadcast the leaderboards for everyone to see.
        """
        print('Showing leaderboards')

        players = botSettings.GetSortedRegisteredPlayers()
        description = ''
        numPlayers = len(players)
        maxPlayersPerPage = 20 # We can only display so many names on a single message
        numPages = math.ceil(numPlayers / maxPlayersPerPage)
        title = '{} Leaderboard'.format(botSettings.guild.name)
        footer = '{} player{}'.format(numPlayers, '' if numPlayers == 1 else 's')

        # sanitize the input to keep the rest simpler
        page = max(1, min(page, numPages))

        if (numPages > 1):
            title += ' [{}/{}]'.format(page, numPages)
    
        # Determine which subset of players to display
        startIndex = 0
        endIndex = maxPlayersPerPage
        if (page > 1):
            startIndex = maxPlayersPerPage * (page - 1)
            endIndex = startIndex + maxPlayersPerPage 

        # Make sure we aren't trying to get more players than are available
        if (endIndex > numPlayers):
            endIndex = numPlayers

        playersOnPage = players[startIndex:endIndex]
        rank = startIndex + 1
        isFirst = True

        for player in playersOnPage:
            if (isFirst):
                isFirst = False
            else:
                description += '\n'

            description += '{}. {} - `{}`'.format(rank, player.name, player.mmr)
            rank += 1

        if (numPlayers == 0):
            await SendMessage(interaction, title=title, description='There are currently no registered players.', color=discord.Color.blue(), ephemeral=not broadcast)
        else:
            await SendMessage(interaction, title=title, description=description, footer=footer, color=discord.Color.blue(), ephemeral=not broadcast)

    @GuildCommand(name='recallmatch')
    @IsAdmin()
    @app_commands.describe(match_id='The unique ID of the match you want to modify. This will be the ID shown in any of the various match related messages.', 
        new_result_type='The new result you want to match to have.')
    @app_commands.choices(new_result_type=[
        Choice(name='Cancelled', value=MatchResult.CANCELLED.value),
        Choice(name='Blue Win', value=MatchResult.TEAM1VICTORY.value),
        Choice(name='Orange Win', value=MatchResult.TEAM2VICTORY.value) ])
    async def OnRecallMatch(self, interaction:discord.Interaction, match_id:int, new_result_type:Choice[int]):
        """Lets you change the a match's result

           **int:** <matchID>
           The unique ID of the match you want to modify. This will be the ID shown in any of the various match related messages.

           **string|int:** <newResult>
           The new result you want to match to have.
           Available results (not case sensitive):
           - 0 (Team 1 Victory)
           - 1 (Team 2 Victory)
           - 2 (Cancelled)
           - blue (Team 1 Victory)
           - team1 (Team 1 Victory)
           - t1 (Team 1 Victory)
           - orange (Team 2 Victory)
           - team2 (Team 2 Victory)
           - t2 (Team 2 Victory)
           - cancel (Cancelled)
        """
        print('User {} is recalling the match {} with a new result: {}'.format(interaction.user, match_id, new_result_type.value))

        new_result = await MatchResult.convert(new_result_type.value)

        if (new_result == MatchResult.INVALID):
            raise InvalidMatchResult(new_result)

        # Get the match from the database if it exists
        match = MatchHistoryData.objects(_matchUniqueID=match_id).first()

        # The match ID is either invalid or we have no records of the match
        if (match is None):
            raise MatchIDNotFound(match_id)

        if (match._result == new_result.value):
            raise MatchResultIdentical(new_result)

        await SendMessage(interaction, description='Recalling match {} with a new result: {}'.format(match_id, new_result_type.name), color=discord.Color.blue())

        def GetTeamField(teamName:str, teamResult:TeamResult):
            teamField = {}
            teamField['name'] = '{}: Team {}'.format('Winner' if teamResult == TeamResult.WIN else 'Loser', teamName)
            teamField['value'] = ''
            teamField['inline'] = False

            if (teamResult == TeamResult.CANCEL):
                teamField['name'] = ' Team {}'.format(teamName)

            return teamField

        def AddToField(field, isFirst, id, sign, oldMMR, delta, newMMR, oldRole, newRole):
            if (isFirst):
                isFirst = False
            else:
                field['value'] += '\n'

            field['value'] += '**{}** {} {} {} = {}'.format(botSettings.GetUserNameByID(id), oldMMR, sign, delta, newMMR)

            if (oldRole is not None and newRole is not None):
                field['value'] += ' **Rank:** {0.mention} -> {1.mention}'.format(oldRole.role, newRole.role)

            return isFirst

        team1Name = 'Blue :blue_square:'
        team2Name = 'Orange :orange_square:'
        title = 'Match Results: Game #{}'.format(match_id)
        footer = 'This match was re-called by {}'.format(interaction.user)

        players = []

        # Determine the team results for before and after to guide how we update the data
        team1PrevResult = TeamResult.WIN if match._result == MatchResult.TEAM1VICTORY.value else TeamResult.LOSE
        team2PrevResult = TeamResult.WIN if match._result == MatchResult.TEAM2VICTORY.value else TeamResult.LOSE
        team1NewResult = TeamResult.WIN if new_result == MatchResult.TEAM1VICTORY else TeamResult.LOSE
        team2NewResult = TeamResult.WIN if new_result == MatchResult.TEAM2VICTORY else TeamResult.LOSE

        if (match._result == MatchResult.CANCELLED.value):
            team1PrevResult = TeamResult.CANCEL
            team2PrevResult = TeamResult.CANCEL
        if (new_result == MatchResult.CANCELLED):
            team1NewResult = TeamResult.CANCEL
            team2NewResult = TeamResult.CANCEL

        team1Field = GetTeamField(team1Name, team1NewResult)
        team2Field = GetTeamField(team2Name, team2NewResult)

        isFirst = True
        for player in match._team1:
            oldDelta = int(player._newMMR - player._prevMMR)
            oldMMR, newMMR, oldRole, newRole = botSettings.RedoMatchByID(player._id, abs(oldDelta), player._mmrDelta, team1PrevResult, team1NewResult)
            player._newMMR = player._prevMMR - oldDelta
            delta = int(abs(newMMR - oldMMR))

            players.append(player._id)

            sign = '+' if team1NewResult == TeamResult.WIN else '-'

            isFirst = AddToField(team1Field, isFirst, player._id, sign, oldMMR, delta, newMMR, oldRole, newRole)
            
        isFirst = True
        for player in match._team2:
            oldDelta = int(player._newMMR - player._prevMMR)
            oldMMR, newMMR, oldRole, newRole = botSettings.RedoMatchByID(player._id, abs(oldDelta), player._mmrDelta, team2PrevResult, team2NewResult)
            player._newMMR = player._prevMMR - oldDelta
            delta = int(abs(newMMR - oldMMR))

            players.append(player._id)

            sign = '+' if team2NewResult == TeamResult.WIN else '-'

            isFirst = AddToField(team2Field, isFirst, player._id, sign, oldMMR, delta, newMMR, oldRole, newRole)

        match._result = new_result.value
        match.save()

        description = '**Creation Time:** {}\n**Map:** {}\n**Map Pool:** {}'.format(match._creationTime, match._map, match._pool)

        if (new_result == MatchResult.TEAM1VICTORY):
            await SendChannelMessage(botSettings.resultsChannel, title=title, description=description, fields=[team1Field, team2Field], footer=footer, color=discord.Color.blue())
        elif (new_result == MatchResult.TEAM2VICTORY):
            await SendChannelMessage(botSettings.resultsChannel, title=title, description=description, fields=[team2Field, team1Field], footer=footer, color=discord.Color.blue())
        else:
            description += '\nnThis match has been cancelled.'
            await SendChannelMessage(botSettings.resultsChannel, title=title, description=description, footer=footer, color=discord.Color.blue())

        # Now we need to refresh roles for all users on both teams
        mmrRoles = botSettings.GetAllMMRRoles()

        if (len(mmrRoles) == 0):
            raise NoMMRRoles()

        for player in players:
            # FakeUser detected
            if (player < 0):
                continue

            member = botSettings.guild.get_member(player)

            # Just ignore users who aren't in the guild
            if (member is None):
                continue

            previousRole, newRole = botSettings.GetMMRRoleByID(player)

            # Remove all their previous mmr roles and readd the correct one
            await RemoveRoles(interaction, member, *mmrRoles, errorMessage='Failed to remove previous rank from {0.mention}. Please try again.'.format(member))
            await AddRoles(interaction, member, newRole.role, botSettings.registeredRole, errorMessage='Failed to add current rank to {0.mention}. Please try again.'.format(member))

        await SendChannelMessage(botSettings.adminChannel, description='The ranks of all players in match #{} have been updated.'.format(match._matchUniqueID), color=discord.Color.blue())

    @GuildCommand(name='forcemap')
    @IsAdmin()
    @app_commands.describe(map='The map you want to force as the next map (or current map if the match has already started).')
    async def OnForceMap(self, interaction:discord.Interaction, map:str):
        """Forces the next/current map
           If there is nobody in queue and there is no match currently being played, this command is ignored. Priority is given to changing the current map if possible and changing the next map second if not.

           **string:** <map>
           The map you want to force as the next map (or current map if the match has already started). This is not case sensitive. No quotes needed.
        """
        print('Forcing map to {}'.format(map))

        if (not botSettings.DoesMapExist(map)):
            raise InvalidMap(map)

        await matchService.ForceMap(interaction, botSettings.GetMapProperName(map))

    @GuildCommand(name='setpool')
    @IsAdmin()
    @app_commands.describe(pool_name='The map pool you want to use for matchmaking.')
    async def OnSetCurrentMapPool(self, interaction:discord.Interaction, pool_name:str):
        """Sets the current Map Pool
           Sets the map pool to use for matchmaking. This will apply on all future matches that haven't already started.

           **string:** <poolName>
           The map pool you want to use for the matchmaking.
        """
        print('Setting map pool to {}'.format(pool_name))

        if (not botSettings.DoesMapPoolExist(pool_name)):
            raise InvalidMapPool(pool_name)

        botSettings.SetCurrentMapPool(pool_name)
        await SendMessage(interaction, description='`{}` has been set as the current map pool.'.format(pool_name), color=discord.Color.blue())

    @GuildCommand(name='forcepool')
    @IsAdmin()
    @app_commands.describe(pool_name='The map pool you want to force for the matchmaking.')
    async def OnForceMapPool(self, interaction:discord.Interaction, pool_name:str):
        """Forces the current Map Pool
           Sets the map pool to use for matchmaking. This will also override the existing map pool if a match has already started, including rerolling the map if the map is not in the new map pool.

           **string:** <pool_name>
           The map pool you want to force for the matchmaking. This is not case sensitive. No quotes needed.
        """
        print('Setting map pool to {}'.format(pool_name))

        if (not botSettings.DoesMapPoolExist(pool_name)):
            raise InvalidMapPool(pool_name)

        if (not matchService.IsMatchInProgress()):
            raise CantForceMapPool()

        botSettings.SetCurrentMapPool(pool_name)
        await SendChannelMessage(interaction.channel, description='`{}` has been set as the current map pool.'.format(pool_name), color=discord.Color.blue())
        await matchService.ForceMapPool(interaction, botSettings.GetMapPoolProperName(pool_name))

    @GuildCommand(name='rerollmap')
    @IsAdmin()
    async def OnRerollMap(self, interaction:discord.Interaction):
        """Rerolls the current map for the match"""
        print('Rerolling the map')

        if (not matchService.IsMatchInProgress()):
            raise CantRerollMap()

        await matchService.RerollMap(interaction, useInteraction=True)

    @GuildCommand(name='swap')
    @IsAdmin()
    @app_commands.describe(player1='One of the players you want to swap. They must be either in the queue or in a match that has already started.', player2='One of the players you want to swap. They must be either in the queue or in a match that has already started.')
    async def OnSwapPlayers(self, interaction:discord.Interaction, player1:discord.Member, player2:discord.Member):
        """Swaps two players between a queue and a match

           **discord.Member:** <player1>
           One of the players you want to swap. They must be either in the queue or in a match that has already started.

           **discord.Member:** <player2>
           One of the players you want to swap. They must be either in the queue or in a match that has already started.
        """
        print('Swapping players {} and {}'.format(player1, player2))

        # Make sure both players are either in a queue or a match
        if (not matchService.IsPlayerQueued(player1) and not matchService.IsPlayerInGame(player1)):
            raise PlayerNotQueuedOrInGame(player1)

        if (not matchService.IsPlayerQueued(player2) and not matchService.IsPlayerInGame(player2)):
            raise PlayerNotQueuedOrInGame(player2)

        # Next validate that they aren't both in queue or both in a match
        if (matchService.IsPlayerQueued(player1) and matchService.IsPlayerQueued(player2)):
            raise PlayersNotSwapable(player1, player2)

        if (matchService.IsPlayerInGame(player1) and matchService.IsPlayerInGame(player2)):
            raise PlayersNotSwapable(player1, player2)

        # Now try to swap
        await matchService.SwapPlayers(interaction, player1, player2)
 
    @GuildCommand(name='removestrat')
    @IsAdmin()
    @app_commands.describe(index='The index of the strat you want to remove.')
    async def OnRemoveStratRouletteStrat(self, interaction:discord.Interaction, index:int):
        """Removes a Strat Roulette strat 
           
           **int:** <index>
           The index of the strat you want to remove.
        """
        if (len(botSettings.strats) == 0):
            raise NoStratRouletteStrats()

        if (index < 0 or index >= len(botSettings.strats)):
            raise InvalidStratIndex(index)

        strat = botSettings.strats[index].strat
        title = botSettings.strats[index].title
        type = await StratRouletteTeamType.convert(botSettings.strats[index].type)
        botSettings.RemoveStratRouletteStrat(index)

        message = '[{}] Strat Removed `[{}] {}`'.format(type.name, title, strat)
        await SendMessage(interaction, description=message, color=discord.Color.blue())

    @OnRecallMatch.error
    @OnRemoveStratRouletteStrat.error
    @OnRemoveMapPoolMap.error
    @OnAddMapPoolMap.error
    @OnSetMapPoolType.error
    @OnRemoveMapPool.error
    @OnAddMapPool.error
    @OnSetMapThumbnail.error
    @OnRemoveMap.error
    @OnAddMap.error
    @OnShowLeaderboards.error
    @OnRefreshUsers.error
    @OnRefreshUser.error
    @OnRemoveRank.error
    @OnUpdateRank.error
    @OnAddRank.error
    @OnSetAdminRole.error
    @OnSetRegisteredRole.error
    @OnShowChannels.error
    @OnSetChannel.error
    @OnClearChannel.error
    @OnForceRegisterPlayer.error
    @OnQuit.error
    @OnClearQueue.error
    @OnForceStartMatch.error
    @OnKickPlayerFromQueue.error
    @OnSetMMR.error
    @OnForceMap.error
    @OnForceMapPool.error
    @OnRerollMap.error
    @OnSwapPlayers.error
    @OnSetCurrentMapPool.error
    async def errorHandling2(self, interaction:discord.Interaction, error:app_commands.AppCommandError):
        await HandleAppError(interaction, error)

