from discord.ext import commands
from data.botsettings import ChannelType, GuildTextChannelMismatch, GuildRoleMismatch , InvalidGuild
from data.playerdata import UserNotRegistered
from data.matchhistorydata import MatchHistoryData, InvalidMatchResult, MatchIDNotFound, MatchResultIdentical, MatchResult
from data.mmrrole import MMRRoleExists, MMRRoleRangeConflict, InvalidMMRRole, NoMMRRoles
from data.siegemap import MapExists, InvalidMap
from services.matchservice import TeamResult
from utils.botutils import IsAdmin, IsValidChannel, AddRoles, RemoveRoles
from utils.errorutils import HandleError
from utils.chatutils import SendMessage, SendChannelMessage
from globals import *
from mongoengine import disconnect
import discord
import math

class AdminCommands(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(name='quit')
	@IsValidChannel(ChannelType.ADMIN)
	@IsAdmin()
	async def OnQuit(self, ctx):
		"""Shuts down the bot"""
		print('User {} has requested a quit. Closing bot.'.format(ctx.author))
		disconnect() # disconect our MongoDB instance
		await self.bot.close() # close our bot instance

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
		"""Kicks a player from the matchmaking queue"""
		print('{} is kicking {} from the queue'.format(ctx.author, member))

		await matchService.KickFromQueue(ctx, member)

	@commands.command(name='forcestartmatch')
	@IsValidChannel(ChannelType.LOBBY)
	@IsAdmin()
	async def OnForceStartMatch(self, ctx):
		"""Starts the match"""
		print('{} is force starting the match'.format(ctx.author))

		await matchService.StartMatch(ctx)

	@commands.command(name='clearchannel')
	@IsValidChannel(ChannelType.ADMIN)
	@IsAdmin()
	async def OnClearChannel(self, ctx, channelType:ChannelType):
		"""Clears a channel from use with the bot"""
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
		"""Sets a channel for use with the bot"""
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
		"""Sets the registered role"""
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
		"""Sets the admin role"""
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
		"""Adds a rank"""
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
		"""Updates a rank's mmr range and delta"""
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
		"""Removes a rank"""
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
		"""Set a player's mmr"""
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

		await SendMessage(ctx, fields=[field], color=discord.Color.blue())

	@commands.command(name='refreshuser')
	@IsValidChannel(ChannelType.ADMIN)
	@IsAdmin()
	async def OnRefreshUser(self, ctx, member:discord.Member):
		"""Refresh a user's roles"""
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
	async def OnAddMap(self, ctx, name:str):
		"""Adds a map"""
		print('Adding map: {}'.format(name))

		if (botSettings.DoesMapExist(name)):
			raise MapExists(name)

		botSettings.AddMap(name)
		await SendMessage(ctx, description='`{}` has been added as a map.'.format(name), color=discord.Color.blue())

	@commands.command(name='removemap')
	@IsValidChannel(ChannelType.ADMIN)
	@IsAdmin()
	async def OnRemoveMap(self, ctx, name:str):
		"""Removes a map"""
		print('Removing map: {}'.format(name))

		if (not botSettings.DoesMapExist(name)):
			raise InvalidMap(name)

		botSettings.RemoveMap(name)
		await SendMessage(ctx, description='`{}` has been removed as a map.'.format(name), color=discord.Color.blue())	

	@commands.command(name='leaderboard')
	@IsValidChannel(ChannelType.ADMIN)
	@IsAdmin()
	async def OnShowLeaderboards(self, ctx, page:int=1):
		"""Shows the leaderboards"""
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
		"""Lets you change the a match's result"""
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

			return teamField

		def AddToField(field, isFirst, id, sign, oldMMR, delta, newMMR, oldRole, newRole):
			if (isFirst):
				isFirst = False
			else:
				field['value'] += '\n'

			field['value'] += '[{}] **MMR:** {} {} {} = {}'.format(botSettings.GetUserNameByID(id), oldMMR, sign, delta, newMMR)

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

		team1Field = GetTeamField(team1Name, team1PrevResult)
		team2Field = GetTeamField(team2Name, team2PrevResult)

		isFirst = True
		for player in match._team1:
			oldMMR, newMMR, oldRole, newRole = botSettings.RedoMatchByID(player._id, player._mmrDelta, team1PrevResult, team1NewResult)
			player._prevMMR = oldMMR
			player._newMMR = newMMR
			delta = int(abs(newMMR - oldMMR))

			players.append(player._id)

			sign = '+' if team1NewResult == TeamResult.WIN else '-'

			isFirst = AddToField(team1Field, isFirst, player._id, sign, oldMMR, delta, newMMR, oldRole, newRole)
			
		isFirst = True
		for player in match._team2:
			oldMMR, newMMR, oldRole, newRole = botSettings.RedoMatchByID(player._id, player._mmrDelta, team2PrevResult, team2NewResult)
			player._prevMMR = oldMMR
			player._newMMR = newMMR
			delta = int(abs(newMMR - oldMMR))

			players.append(player._id)

			sign = '+' if team2NewResult == TeamResult.WIN else '-'

			isFirst = AddToField(team2Field, isFirst, player._id, sign, oldMMR, delta, newMMR, oldRole, newRole)

		match._result = newResult.value
		match.save()

		if (newResult == MatchResult.TEAM1VICTORY):
			await SendChannelMessage(botSettings.resultsChannel, title=title, fields=[team1Field, team2Field], footer=footer, color=discord.Color.blue())
		elif (newResult == MatchResult.TEAM2VICTORY):
			await SendChannelMessage(botSettings.resultsChannel, title=title, fields=[team2Field, team1Field], footer=footer, color=discord.Color.blue())
		else:
			await SendChannelMessage(botSettings.resultsChannel, title=title, description='This match has been cancelled.', footer=footer, color=discord.Color.blue())

		# Now we need to refresh roles for all users on both teams
		mmrRoles = botSettings.GetAllMMRRoles()

		if (len(mmrRoles) == 0):
			raise NoMMRRoles()

		for player in players:
			member = botSettings.guild.get_member(player)

			# Just ignore users who aren't in the guild
			if (member is None):
				continue

			previousRole, newRole = botSettings.GetMMRRoleByID(player)

			# Remove all their previous mmr roles and readd the correct one
			await RemoveRoles(ctx, member, *mmrRoles, errorMessage='Failed to remove previous rank from {0.mention}. Please try again.'.format(member))
			await AddRoles(ctx, member, newRole.role, botSettings.registeredRole, errorMessage='Failed to add current rank to {0.mention}. Please try again.'.format(member))

		await SendChannelMessage(botSettings.adminChannel, description='The ranks of all players in match #{} have been updated.'.format(match._matchUniqueID), color=discord.Color.blue())


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
	async def errorHandling(self, ctx, error):
		await HandleError(ctx, error)
