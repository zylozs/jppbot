from discord.ext import commands
from data.botsettings import ChannelType, GuildTextChannelMismatch, GuildRoleMismatch , InvalidGuild, RegisteredRoleUnitialized, EmptyName
from data.playerdata import UserNotRegistered, UserAlreadyRegistered
from data.matchhistorydata import MatchHistoryData, InvalidMatchResult, MatchIDNotFound, MatchResultIdentical, MatchResult
from data.mmrrole import MMRRoleExists, MMRRoleRangeConflict, InvalidMMRRole, NoMMRRoles
from data.siegemap import MapExists, InvalidMap
from data.mappool import MapPoolExists, InvalidMapPool, MapPoolType, InvalidMapPoolType, InvalidMapPoolMap, MapPoolMapExists
from services.matchservice import TeamResult, PlayerNotQueuedOrInGame, PlayersNotSwapable
from utils.botutils import IsAdmin, IsValidChannel, AddRoles, RemoveRoles
from utils.errorutils import HandleError
from utils.chatutils import SendMessage, SendChannelMessage
from globals import *
from mongoengine import disconnect
import discord
import math
import random

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='quit')
    @IsValidChannel(ChannelType.ADMIN)
    @IsAdmin()
    async def OnQuit(self, ctx):
        """Shuts down the bot"""
        goodbye = ['au revoir', 'goodbye', 'cya', 'à la prochaine']
        await ctx.send(random.choice(goodbye))
        print('User {} has requested a quit. Closing bot.'.format(ctx.author))
        disconnect() # disconect our MongoDB instance
        await self.bot.close() # close our bot instance

    @commands.command(name='forceregister')
    @IsValidChannel(ChannelType.REGISTER)
    @IsAdmin()
    async def OnForceRegisterPlayer(self, ctx, member:discord.Member, initialMMR:int, *name):
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

           **string:** <name>
           The name you want to give the user with the bot. Spaces and special characters are allowed.
        """
        if (len(name) == 0):
            raise EmptyName()

        combinedName = ' '.join(name)
        print('User {0.author} is force registering {1} with name {2} and initial mmr of {3}'.format(ctx, member, combinedName, initialMMR))

        if (botSettings.registeredRole is None):
            raise RegisteredRoleUnitialized()

        if (botSettings.IsUserRegistered(member)):
            raise UserAlreadyRegistered(member)

        try:
            await member.add_roles(botSettings.registeredRole, reason='User {0.name} used the forceregister command'.format(ctx.author))

            botSettings.RegisterUser(member, combinedName)

            botSettings.SetMMR(member, initialMMR)

            await SendMessage(ctx, description='You have registered {0.mention} as `{1}` with an initial MMR of {2}.'.format(member, combinedName, initialMMR), color=discord.Color.blue())
        except discord.HTTPException:
            await SendMessage(ctx, description='Registration failed. Please try again.', color=discord.Color.red())

    @commands.command(name='clearqueue')
    @IsValidChannel(ChannelType.LOBBY)
    @IsAdmin()
    async def OnClearQueue(self, ctx):
        """Clears the matchmaking queue"""
        print('Clearing queue')

        await matchService.ClearQueue(ctx)

    @commands.command(name='kick')
    @IsValidChannel(ChannelType.LOBBY)
    @IsAdmin()
    async def OnKickPlayerFromQueue(self, ctx, member:discord.Member):
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
        print('{} is kicking {} from the queue'.format(ctx.author, member))

        await matchService.KickFromQueue(ctx, member)

    @commands.command(name='forcestartmatch')
    @IsValidChannel(ChannelType.LOBBY)
    @IsAdmin()
    async def OnForceStartMatch(self, ctx, fillWithFakePlayers:bool = False):
        """Starts the match
        
           **bool:** <fillWithFakePlayers>
           Fills the lobby with fake players. This is useful for testing bot functionality without having 10 players. **DO NOT USE IN A REAL MATCH**
        """
        print('{} is force starting the match {}'.format(ctx.author, 'and filling with fake users' if fillWithFakePlayers else ''))

        await matchService.StartMatch(ctx, fillWithFakePlayers)

    @commands.command(name='clearchannel')
    @IsValidChannel(ChannelType.ADMIN)
    @IsAdmin()
    async def OnClearChannel(self, ctx, channelType:ChannelType):
        """Clears a channel from use with the bot

           **string:** <channelType>
           Types available (not case sensitive):
           - lobby
           - register
           - results
           - report
           - admin
        """
        print('Channel type: {}'.format(channelType))

        if (channelType is ChannelType.LOBBY):
            channel = botSettings.lobbyChannel
            botSettings.SetLobbyChannel(None)
        elif (channelType is ChannelType.REGISTER):
            channel = botSettings.registerChannel
            botSettings.SetRegisterChannel(None)
        elif (channelType is ChannelType.ADMIN):
            channel = botSettings.adminChannel
            botSettings.SetAdminChannel(None)
        elif (channelType is ChannelType.RESULTS):
            channel = botSettings.resultsChannel
            botSettings.SetResultsChannel(None)
        elif (channelType is ChannelType.REPORT):
            channel = botSettings.reportChannel
            botSettings.SetReportChannel(None)

        await SendMessage(ctx, description='{0.mention} has been cleared as the {1.value} channel'.format(channel, channelType), color=discord.Color.blue())

    @commands.command(name='setchannel')
    @IsValidChannel(ChannelType.ADMIN)
    @IsAdmin()
    async def OnSetChannel(self, ctx, channel:discord.TextChannel, channelType:ChannelType):
        """Sets a channel for use with the bot

           **discord.TextChannel:** <channel>
           The text channel you want to use.
           You can use any of the following to identify it:
           - ID (i.e. 123456789)
           - mention (i.e. #Name)
           - name (i.e. Name  (case sensitive)

           **string:** <channelType>
           Types available (not case sensitive):
           - lobby
           - register
           - results
           - report
           - admin
        """
        print('Setting Channel: {} type: {}'.format(channel, channelType))

        # setup guild if missing
        if (botSettings.guild is None):
            botSettings.SetGuild(channel.guild)
        elif (botSettings.guild is not channel.guild):
            raise GuildTextChannelMismatch(channel)

        if (channelType is ChannelType.LOBBY):
            botSettings.SetLobbyChannel(channel)
        elif (channelType is ChannelType.REGISTER):
            botSettings.SetRegisterChannel(channel)
        elif (channelType is ChannelType.ADMIN):
            botSettings.SetAdminChannel(channel)
        elif (channelType is ChannelType.RESULTS):
            botSettings.SetResultsChannel(channel)
        elif (channelType is ChannelType.REPORT):
            botSettings.SetReportChannel(channel)

        await SendMessage(ctx, description='{0.mention} has been set as the {1.value} channel'.format(channel, channelType), color=discord.Color.blue())

    @commands.command(name='channels')
    @IsValidChannel(ChannelType.ADMIN)
    @IsAdmin()
    async def OnShowChannels(self, ctx):
        """Shows the channels used by the bot"""
        print('Showing channels')

        description='Lobby Channel: {}\n'.format('Not setup' if botSettings.lobbyChannel is None else botSettings.lobbyChannel.mention)
        description+='Register Channel: {}\n'.format('Not setup' if botSettings.registerChannel is None else botSettings.registerChannel.mention)
        description+='Report Channel: {}\n'.format('Not setup' if botSettings.reportChannel is None else botSettings.reportChannel.mention)
        description+='Results Channel: {}\n'.format('Not setup' if botSettings.resultsChannel is None else botSettings.resultsChannel.mention)
        description+='Admin Channel: {}'.format('Not setup' if botSettings.adminChannel is None else botSettings.adminChannel.mention)

        await SendMessage(ctx, description=description, color=discord.Color.blue())

    @commands.command(name='setregisteredrole')
    @IsValidChannel(ChannelType.ADMIN)
    @IsAdmin()
    async def OnSetRegisteredRole(self, ctx, role:discord.Role):
        """Sets the registered role

           **discord.Role:** <role>
           The role you want to use for registered players.
           You can use any of the following to identify it:
           - ID (i.e. 123456789)
           - mention (i.e. @RoleName)
           - name (i.e. RoleName  (case sensitive)
        """
        print('Setting Registered Role: {}'.format(role))

        # setup guild if missing
        if (botSettings.guild is None):
            botSettings.SetGuild(role.guild)
        elif (botSettings.guild is not role.guild):
            raise GuildRoleMismatch(role)

        if (botSettings.registeredRole is not None):
            title = 'Warning: You are changing the registered role.'
            description = 'This will not affect players who are already registered. The previous role {0.mention} will not be automatically changed on registered players, however the role is purely cosmetic.'.format(botSettings.registeredRole)
            await SendMessage(ctx, title=title, description=description, color=discord.Color.gold())

        botSettings.SetRegisteredRole(role)
        await SendMessage(ctx, description='The registered role has been updated.', color=discord.Color.blue())

    @commands.command(name='setadminrole')
    @commands.has_permissions(administrator=True)
    @IsValidChannel(ChannelType.ADMIN)
    async def OnSetAdminRole(self, ctx, role:discord.Role):
        """Sets the admin role

           **discord.Role:** <role>
           The role you want to use to give admin priviledges with the bot.
           You can use any of the following to identify it:
           - ID (i.e. 123456789)
           - mention (i.e. @RoleName)
           - name (i.e. RoleName  (case sensitive)
        """
        print('Setting Admin Role: {}'.format(role))

        # setup guild if missing
        if (botSettings.guild is None):
            botSettings.SetGuild(role.guild)
        elif (botSettings.guild is not role.guild):
            raise GuildRoleMismatch(role)

        if (botSettings.adminRole is not None):
            title = 'Warning: You are changing the admin role.'
            description = 'This may impact members with the previous admin role {0.mention}. They will need their role updated to regain admin priviledges with the bot.'.format(botSettings.adminRole)
            await SendMessage(ctx, title=title, description=description, color=discord.Color.gold())

        botSettings.SetAdminRole(role)
        await SendMessage(ctx, description='The admin role has been updated.', color=discord.Color.blue())

    @commands.command(name='addrank')
    @IsValidChannel(ChannelType.ADMIN)
    @IsAdmin()
    async def OnAddRank(self, ctx, role:discord.Role, mmrMin:int, mmrMax:int, mmrDelta:int):
        """Adds a rank

           **discord.Role:** <role>
           The role you want to use for a rank.
           You can use any of the following to identify it:
           - ID (i.e. 123456789)
           - mention (i.e. @RoleName)
           - name (i.e. RoleName  (case sensitive)

           **int:** <mmrMin>
           The minimum MMR for this rank (inclusive)

           **int:** <mmrMax>
           The maximum MMR for this rank (inclusive)

           **int:** <mmrDelta>
           The MMR increase or decrease after each match
        """
        print('Adding new rank: {} min: {} max: {} delta: {}'.format(role, mmrMin, mmrMax, mmrDelta))

        # setup guild if missing
        if (botSettings.guild is None):
            botSettings.SetGuild(role.guild)
        elif (botSettings.guild is not role.guild):
            raise GuildRoleMismatch(role)

        if (botSettings.IsValidMMRRole(role)):
            raise MMRRoleExists(role)

        if (not botSettings.IsMMRRoleRangeValid(mmrMin, mmrMax)):
            raise MMRRoleRangeConflict()

        botSettings.AddMMRRole(role, mmrMin, mmrMax, mmrDelta)
        await SendMessage(ctx, title='New Rank Added', description='Role: {0.mention}\nMMR Range: {1}-{2}\nMMR Delta: +-{3}'.format(role, mmrMin, mmrMax, mmrDelta), color=discord.Color.blue())

    @commands.command(name='updaterank')
    @IsValidChannel(ChannelType.ADMIN)
    @IsAdmin()
    async def OnUpdateRank(self, ctx, role:discord.Role, mmrMin:int, mmrMax:int, mmrDelta:int):
        """Updates a rank's mmr range and delta

           **discord.Role:** <role>
           The role associated with the rank you want to update
           You can use any of the following to identify it:
           - ID (i.e. 123456789)
           - mention (i.e. @RoleName)
           - name (i.e. RoleName  (case sensitive)

           **int:** <mmrMin>
           The minimum MMR for this rank (inclusive)

           **int:** <mmrMax>
           The maximum MMR for this rank (inclusive)

           **int:** <mmrDelta>
           The MMR increase or decrease after each match
        """
        print('Updating existing rank: {} min: {} max: {} delta: {}'.format(role, mmrMin, mmrMax, mmrDelta))

        # setup guild if missing
        if (botSettings.guild is None):
            botSettings.SetGuild(role.guild)
        elif (botSettings.guild is not role.guild):
            raise GuildRoleMismatch(role)

        if (not botSettings.IsValidMMRRole(role)):
            raise InvalidMMRRole(role)

        if (not botSettings.IsMMRRoleRangeValid(mmrMin, mmrMax)):
            raise MMRRoleRangeConflict()

        botSettings.UpdateMMRRole(role, mmrMin, mmrMax, mmrDelta)
        await SendMessage(ctx, title='Rank Updated', description='Role: {0.mention}\nMMR Range: {1}-{2}\nMMR Delta: +-{3}'.format(role, mmrMin, mmrMax, mmrDelta), color=discord.Color.blue())

    @commands.command(name='removerank')
    @IsValidChannel(ChannelType.ADMIN)
    @IsAdmin()
    async def OnRemoveRank(self, ctx, role:discord.Role):
        """Removes a rank

           **discord.Role:** <role>
           The role associated with the rank you want to remove 
           You can use any of the following to identify it:
           - ID (i.e. 123456789)
           - mention (i.e. @RoleName)
           - name (i.e. RoleName  (case sensitive)
        """
        print('Removing rank: {}'.format(role))

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
            member = botSettings.guild.get_member(player.user.id)
            if member is not None and role in member.roles:
                await RemoveRoles(ctx, member, role, errorMessage='Failed to remove rank. Please try again.')

        botSettings.RemoveMMRRole(role)
        await SendMessage(ctx, title='Rank Removed', description='Role: {0.mention}\nMMR Range: {1}-{2}\nMMR Delta: +-{3}'.format(role, mmrMin, mmrMax, mmrDelta), color=discord.Color.blue())

    @commands.command(name='setmmr')
    @IsValidChannel(ChannelType.ADMIN)
    @IsAdmin()
    async def OnSetMMR(self, ctx, member:discord.Member, mmr:int):
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
            await RemoveRoles(ctx, member, previousRole.role, errorMessage='Failed to remove previous rank. Please try again.')
        
        if (newRole is not None):
            await AddRoles(ctx, member, newRole.role, errorMessage='Failed to add new rank. Please try again.')

        field = {}
        field['name'] = 'MMR Updated'
        field['value'] = 'Player: {0.mention}:\nMMR: {1} -> {2}'.format(member, previousMMR, mmr)
        field['inline'] = False

        if (previousRole is None and newRole is not None):
            field['value'] += '\nRank: {0.mention}'.format(newRole.role)
        elif (previousRole is not None and newRole is not None):
            field['value'] += '\nRank: {0.mention} -> {1.mention}'.format(previousRole.role, newRole.role)

        matchService.UpdateMMR(member, mmr)

        await SendMessage(ctx, fields=[field], color=discord.Color.blue())

    @commands.command(name='refreshuser')
    @IsValidChannel(ChannelType.ADMIN)
    @IsAdmin()
    async def OnRefreshUser(self, ctx, member:discord.Member):
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
        await RemoveRoles(ctx, member, *mmrRoles, errorMessage='Failed to remove previous rank from {0.mention}. Please try again.'.format(member))
        await AddRoles(ctx, member, newRole.role, botSettings.registeredRole, errorMessage='Failed to add current rank to {0.mention}. Please try again.'.format(member))
    
        await SendMessage(ctx, description='Ranks have been updated on {0.mention}'.format(member), color=discord.Color.blue())

    @commands.command(name='refreshusers')
    @IsValidChannel(ChannelType.ADMIN)
    @IsAdmin()
    async def OnRefreshUsers(self, ctx):
        """Refresh all user roles"""
        print('Refreshing roles on all users')

        if (botSettings.guild is None):
            raise InvalidGuild()

        mmrRoles = botSettings.GetAllMMRRoles()

        if (len(mmrRoles) == 0):
            raise NoMMRRoles()

        for player in botSettings.registeredPlayers.values():
            previousRole, newRole = botSettings.GetMMRRole(player.user)

            member = botSettings.guild.get_member(player.user.id)

            # Just ignore users who aren't in the guild
            if (member is None):
                continue

            # Remove all their previous mmr roles and readd the correct one
            await RemoveRoles(ctx, member, *mmrRoles, errorMessage='Failed to remove previous rank from {0.mention}. Please try again.'.format(member))
            await AddRoles(ctx, member, newRole.role, botSettings.registeredRole, errorMessage='Failed to add current rank to {0.mention}. Please try again.'.format(member))

        await SendMessage(ctx, description='Ranks have been updated on all registered players.', color=discord.Color.blue())

    @commands.command(name='addmap')
    @IsValidChannel(ChannelType.ADMIN)
    @IsAdmin()
    async def OnAddMap(self, ctx, name:str, thumbnailURL:str =''):
        """Adds a map

           **string:** <name>
           The name of the map you want to add. Casing is preserved, but name validation is not case sensitive.

           **string:** <thumbnailURL> (Optional)
           **Default value:** ''
           The url of the image you want to use as the map's thumbnail. Omit if you dont want a thumbnail.
        """
        print('Adding map {} with thumbnail {}'.format(name, thumbnailURL))

        if (botSettings.DoesMapExist(name)):
            raise MapExists(name)

        botSettings.AddMap(name, thumbnailURL)
        await SendMessage(ctx, description='`{}` has been added as a map.'.format(name), color=discord.Color.blue())

    @commands.command(name='removemap')
    @IsValidChannel(ChannelType.ADMIN)
    @IsAdmin()
    async def OnRemoveMap(self, ctx, name:str):
        """Removes a map
        
           **string:** <name>
           The name of the map you want to remove. This is not case sensitive. 
        """
        print('Removing map: {}'.format(name))

        if (not botSettings.DoesMapExist(name)):
            raise InvalidMap(name)

        botSettings.RemoveMap(name)
        await SendMessage(ctx, description='`{}` has been removed as a map.'.format(name), color=discord.Color.blue())	

    @commands.command(name='setmapthumbnail')
    @IsValidChannel(ChannelType.ADMIN)
    @IsAdmin()
    async def OnSetMapThumbnail(self, ctx, name:str, thumbnailURL:str):
        """Changes the thumbnail for a map

           **string:** <name>
           The name of the map you want to add. This is not case sensitive. 

           **string:** <thumbnailURL>
           The url of the image you want to use as the map's thumbnail. 
        """
        print('Setting thumbnail for map {} to {}'.format(name, thumbnailURL))

        if (not botSettings.DoesMapExist(name)):
            raise InvalidMap(name)

        botSettings.SetMapThumbnail(name, thumbnailURL)
        await SendMessage(ctx, description='`{}` has been set as the thumbnail for map {}.'.format(thumbnailURL, name), color=discord.Color.blue())	

    @commands.command(name='addpool')
    @IsValidChannel(ChannelType.ADMIN)
    @IsAdmin()
    async def OnAddMapPool(self, ctx, type:MapPoolType, *name):
        """Adds a map pool

           **string|int:** <type>
           The type of Map Pool you want to have.
           Available results (not case sensitive):
           - 0 (All maps)
           - 1 (Custom map list)
           - all (All maps)
           - a (All maps)
           - custom (Custom map list)
           - c (Custom map list)

           **string:** <name>
           The name of the map pool you want to add. Casing is preserved, but name validation is not case sensitive.
        """

        if (type == MapPoolType.INVALID):
            raise InvalidMapPoolType(type)

        if (len(name) == 0):
            raise EmptyName()

        combinedName = ' '.join(name)

        if (botSettings.DoesMapPoolExist(combinedName)):
            raise MapPoolExists(combinedName)

        botSettings.AddMapPool(combinedName, type.value)
        await SendMessage(ctx, description='`{}` has been added as a map pool.'.format(combinedName), color=discord.Color.blue())

    @commands.command(name='removepool')
    @IsValidChannel(ChannelType.ADMIN)
    @IsAdmin()
    async def OnRemoveMapPool(self, ctx, *name):
        """Removes a map pool
        
           **string:** <name>
           The name of the map pool you want to remove. This is not case sensitive. 
        """

        if (len(name) == 0):
            raise EmptyName()

        combinedName = ' '.join(name)

        if (not botSettings.DoesMapPoolExist(combinedName)):
            raise InvalidMapPool(combinedName)

        botSettings.RemoveMapPool(combinedName)
        await SendMessage(ctx, description='`{}` has been removed as a map pool.'.format(combinedName), color=discord.Color.blue())

    @commands.command(name='setpooltype')
    @IsValidChannel(ChannelType.ADMIN)
    @IsAdmin()
    async def OnSetMapPoolType(self, ctx, type:MapPoolType, *name):
        """Sets an existing map pool's type

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

           **string:** <name>
           The name of the map pool you want to modify. This is not case sensitive.
        """
        if (type == MapPoolType.INVALID):
            raise InvalidMapPoolType(type)

        if (len(name) == 0):
            raise EmptyName()

        combinedName = ' '.join(name)

        if (not botSettings.DoesMapPoolExist(combinedName)):
            raise InvalidMapPool(combinedName)

        botSettings.pools[combinedName.lower()].SetType(type.value)
        await SendMessage(ctx, description='`{}` has changed Map Pool type to `{}`'.format(combinedName, type.name), color=discord.Color.blue())

    @commands.command(name='addpoolmap')
    @IsValidChannel(ChannelType.ADMIN)
    @IsAdmin()
    async def OnAddMapPoolMap(self, ctx, mapName:str, *poolName):
        """Adds a map to a map pool

           **string:** <mapName>
           The name of the map you want to add. This is not case sensitive.

           **string:** <poolName>
           The name of the map pool you want to add it to. This is not case sensitive.
        """

        if (not botSettings.DoesMapExist(mapName)):
            raise InvalidMap(mapName)

        mapProperName = botSettings.GetMapProperName(mapName)

        if (len(poolName) == 0):
            raise EmptyName()

        combinedPoolName = ' '.join(poolName)

        if (not botSettings.DoesMapPoolExist(combinedPoolName)):
            raise InvalidMapPool(combinedPoolName)

        if (botSettings.DoesMapPoolMapExist(combinedPoolName, mapProperName)):
            raise MapPoolMapExists(combinedPoolName, mapProperName)

        botSettings.AddMapPoolMap(combinedPoolName, mapProperName)
        await SendMessage(ctx, description='`{}` has been added to map pool `{}`.'.format(mapProperName, combinedPoolName), color=discord.Color.blue())

    @commands.command(name='removepoolmap')
    @IsValidChannel(ChannelType.ADMIN)
    @IsAdmin()
    async def OnRemoveMapPoolMap(self, ctx, mapName:str, *poolName):
        """Removes a map from a map pool

           **string:** <mapName>
           The name of the map you want to remove. This is not case sensitive.

           **string:** <poolName>
           The name of the map pool you want to remove it from. This is not case sensitive.
        """
        if (not botSettings.DoesMapExist(mapName)):
            raise InvalidMap(mapName)

        mapProperName = botSettings.GetMapProperName(mapName)

        if (len(poolName) == 0):
            raise EmptyName()

        combinedPoolName = ' '.join(poolName)

        if (not botSettings.DoesMapPoolExist(combinedPoolName)):
            raise InvalidMapPool(combinedPoolName)

        if (not botSettings.DoesMapPoolMapExist(combinedPoolName, mapProperName)):
            raise InvalidMapPoolMap(combinedPoolName, mapProperName)

        botSettings.RemoveMapPoolMap(combinedPoolName, mapProperName)
        await SendMessage(ctx, description='`{}` has been removed from map pool `{}`.'.format(mapProperName, combinedPoolName), color=discord.Color.blue())
    
    @commands.command(name='leaderboard')
    @IsValidChannel(ChannelType.ADMIN)
    @IsAdmin()
    async def OnShowLeaderboards(self, ctx, page:int=1):
        """Shows the leaderboards
        
           **int:** <page>
           **Default value:** 1
           The page of the leaderboards you want to show.
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
            await SendMessage(ctx, title=title, description='There are currently no registered players.', color=discord.Color.blue())
        else:
            await SendMessage(ctx, title=title, description=description, footer=footer, color=discord.Color.blue())

    @commands.command('recallmatch')
    @IsValidChannel(ChannelType.REPORT)
    @IsAdmin()
    async def OnRecallMatch(self, ctx, matchID:int, newResult:MatchResult):
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
        print('User {} is recalling the match {} with a new result: {}'.format(ctx.author, matchID, newResult))

        if (newResult == MatchResult.INVALID):
            raise InvalidMatchResult(newResult)

        # Get the match from the database if it exists
        match = MatchHistoryData.objects(_matchUniqueID=matchID).first()

        # The match ID is either invalid or we have no records of the match
        if (match is None):
            raise MatchIDNotFound(matchID)

        if (match._result == newResult.value):
            raise MatchResultIdentical(newResult)

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
        title = 'Match Results: Game #{}'.format(matchID)
        footer = 'This match was re-called by {}'.format(ctx.author)

        players = []

        # Determine the team results for before and after to guide how we update the data
        team1PrevResult = TeamResult.WIN if match._result == MatchResult.TEAM1VICTORY.value else TeamResult.LOSE
        team2PrevResult = TeamResult.WIN if match._result == MatchResult.TEAM2VICTORY.value else TeamResult.LOSE
        team1NewResult = TeamResult.WIN if newResult == MatchResult.TEAM1VICTORY else TeamResult.LOSE
        team2NewResult = TeamResult.WIN if newResult == MatchResult.TEAM2VICTORY else TeamResult.LOSE

        if (match._result == MatchResult.CANCELLED.value):
            team1PrevResult = TeamResult.CANCEL
            team2PrevResult = TeamResult.CANCEL
        if (newResult == MatchResult.CANCELLED):
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

        match._result = newResult.value
        match.save()

        description = '**Creation Time:** {}\n**Map:** {}\n**Map Pool:** {}'.format(match._creationTime, match._map, match._pool)

        if (newResult == MatchResult.TEAM1VICTORY):
            await SendChannelMessage(botSettings.resultsChannel, title=title, description=description, fields=[team1Field, team2Field], footer=footer, color=discord.Color.blue())
        elif (newResult == MatchResult.TEAM2VICTORY):
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
            await RemoveRoles(ctx, member, *mmrRoles, errorMessage='Failed to remove previous rank from {0.mention}. Please try again.'.format(member))
            await AddRoles(ctx, member, newRole.role, botSettings.registeredRole, errorMessage='Failed to add current rank to {0.mention}. Please try again.'.format(member))

        await SendChannelMessage(botSettings.adminChannel, description='The ranks of all players in match #{} have been updated.'.format(match._matchUniqueID), color=discord.Color.blue())

    @commands.command('forcemap')
    @IsValidChannel(ChannelType.LOBBY)
    @IsAdmin()
    async def OnForceMap(self, ctx, map:str):
        """Forces the next/current map
           If there is nobody in queue and there is no match currently being played, this command is ignored. Priority is given to changing the current map if possible and changing the next map second if not.

           **string:** <map>
           The map you want to force as the next map (or current map if the match has already started).
        """
        print('Forcing map to {}'.format(map))

        if (not botSettings.DoesMapExist(map)):
            raise InvalidMap(map)

        await matchService.ForceMap(ctx, botSettings.GetMapProperName(map))

    @commands.command('setpool')
    @IsValidChannel(ChannelType.LOBBY)
    @IsAdmin()
    async def OnSetCurrentMapPool(self, ctx, *poolName):
        """Sets the current Map Pool
           Sets the map pool to use for matchmaking. This will apply on all future matches that haven't already started.

           **string:** <poolName>
           The map pool you want to use for the matchmaking.
        """
        if (len(poolName) == 0):
            raise EmptyName()

        combinedPoolName = ' '.join(poolName)
        print('Setting map pool to {}'.format(combinedPoolName))

        if (not botSettings.DoesMapPoolExist(combinedPoolName)):
            raise InvalidMapPool(combinedPoolName)

        botSettings.SetCurrentMapPool(combinedPoolName)
        await SendMessage(ctx, description='`{}` has been set as the current map pool.'.format(combinedPoolName), color=discord.Color.blue())

    @commands.command('forcepool')
    @IsValidChannel(ChannelType.LOBBY)
    @IsAdmin()
    async def OnForceMapPool(self, ctx, *poolName):
        """Forces the current Map Pool
           Sets the map pool to use for matchmaking. This will also override the existing map pool if a match has already started, including rerolling the map if the map is not in the new map pool.

           **string:** <poolName>
           The map pool you want to force for the matchmaking.
        """

        if (len(poolName) == 0):
            raise EmptyName()

        combinedPoolName = ' '.join(poolName)
        print('Setting map pool to {}'.format(combinedPoolName))

        if (not botSettings.DoesMapPoolExist(combinedPoolName)):
            raise InvalidMapPool(combinedPoolName)

        botSettings.SetCurrentMapPool(combinedPoolName)
        await matchService.ForceMapPool(ctx, botSettings.GetMapPoolProperName(combinedPoolName))
        await SendMessage(ctx, description='`{}` has been set as the current map pool.'.format(combinedPoolName), color=discord.Color.blue())

    @commands.command('rerollmap')
    @IsValidChannel(ChannelType.LOBBY)
    @IsAdmin()
    async def OnRerollMap(self, ctx):
        """Rerolls the current map for the match"""
        print('Rerolling the map')

        await matchService.RerollMap(ctx)

    @commands.command('swap')
    @IsValidChannel(ChannelType.LOBBY)
    @IsAdmin()
    async def OnSwapPlayers(self, ctx, player1:discord.Member, player2:discord.Member):
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
        await matchService.SwapPlayers(ctx, player1, player2)

    @OnQuit.error
    @OnClearQueue.error
    @OnKickPlayerFromQueue.error
    @OnForceStartMatch.error
    @OnClearChannel.error
    @OnSetChannel.error
    @OnShowChannels.error
    @OnSetRegisteredRole.error
    @OnSetAdminRole.error
    @OnAddRank.error
    @OnUpdateRank.error
    @OnRemoveRank.error
    @OnSetMMR.error
    @OnRefreshUser.error
    @OnRefreshUsers.error
    @OnAddMap.error
    @OnRemoveMap.error
    @OnShowLeaderboards.error
    @OnRecallMatch.error
    @OnForceMap.error
    @OnRerollMap.error
    @OnSetMapThumbnail.error
    @OnForceRegisterPlayer.error
    @OnSwapPlayers.error
    @OnAddMapPool.error
    @OnRemoveMapPool.error
    @OnSetMapPoolType.error
    @OnAddMapPoolMap.error
    @OnRemoveMapPoolMap.error
    @OnSetCurrentMapPool.error
    @OnForceMapPool.error
    async def errorHandling(self, ctx, error):
        await HandleError(ctx, error)

