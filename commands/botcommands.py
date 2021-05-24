import discord
from data.botsettings import BotSettings, ChannelType, ChannelTypeInvalid, GuildTextChannelMismatch, GuildRoleMismatch, RegisteredRoleUnitialized, AdminRoleUnitialized, InvalidGuild, InvalidCommandChannel
from data.mmrrole import InvalidMMRRole, MMRRoleExists, MMRRoleRangeConflict, NoMMRRoles
from data.siegemap import MapExists, InvalidMap 
from data.playerdata import UserNotRegistered, UserAlreadyRegistered
from data.matchhistorydata import MatchResult, InvalidMatchResult, MatchHistoryData, MatchIDNotFound, MatchResultIdentical
from services.matchservice import MatchService, PlayerAlreadyQueued, PlayerNotQueued, TeamResult
from utils.chatutils import SendMessage, SendChannelMessage
from discord.ext import commands
from mongoengine import connect, disconnect
import math

# Connect to our MongoDB
connect(db="jppbot")

# Load (or create) our settings
if (len(BotSettings.objects) > 0):
	botSettings = BotSettings.objects.first()
else:
	botSettings = BotSettings()

bot = commands.Bot(command_prefix='!', description='A bot to host the weekly JPP sessions.')

matchService = MatchService()
matchService.Init(bot, botSettings)

def IsValidChannel(channelType:ChannelType, includeAdmin=True):
	async def predicate(ctx):
		if (not botSettings.IsValidChannel(ctx.channel, channelType, includeAdmin=includeAdmin)):
			raise InvalidCommandChannel(ctx.channel, channelType)
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

@bot.event
async def on_ready():
	print('We have logged in as {0.user}'.format(bot))
	await botSettings.InitSettings(bot)

@bot.command(name='quit')
@commands.has_permissions(administrator=True)
async def OnQuit(ctx):
	disconnect() # disconect our MongoDB instance
	await bot.close() # close our bot instance

@bot.command(name='jpp')
async def OnJPP(ctx):
	await ctx.send(':jpp:')

@bot.command(name='register', aliases=['r'])
@IsValidChannel(ChannelType.REGISTER)
async def OnRegisterPlayer(ctx, name:str):
	print('User {0.author} is registering with name {1}'.format(ctx, name))

	if (botSettings.registeredRole is None):
		raise RegisteredRoleUnitialized()

	if (botSettings.IsUserRegistered(ctx.author)):
		raise UserAlreadyRegistered(ctx.author)

	try:
		await ctx.author.add_roles(botSettings.registeredRole, reason='User {0.name} used the register command'.format(ctx.author))

		botSettings.RegisterUser(ctx.author, name)

		await SendMessage(ctx, description='You have been registered as `{}`!'.format(name), color=discord.Color.blue())
	except discord.HTTPException:
		await SendMessage(ctx, description='Registration failed. Please try again.', color=discord.Color.red())

@bot.command(name='setname')
async def OnSetName(ctx, name:str):
	print('User {0.author} is changing their name to {1}'.format(ctx, name))

	if (not botSettings.IsUserRegistered(ctx.author)):
		raise UserNotRegistered(ctx.author)

	botSettings.ChangeName(ctx.author, name)

@bot.command(name='registeradmin')
@commands.has_permissions(administrator=True)
@IsValidChannel(ChannelType.ADMIN)
async def OnRegisterAdmin(ctx, member:discord.Member):
	print('User {0.author} is registering a new admin {1}'.format(ctx, member))

	if (botSettings.adminRole is None):
		raise AdminRoleUnitialized()

	try:
		await member.add_roles(botSettings.adminRole, reason='User {0.author} is registering a new admin {1}'.format(ctx, member))
		await SendMessage(ctx, description='You have registered {0.mention} as an admin!'.format(member), color=discord.Color.blue())
	except discord.HTTPException:
		await SendMessage(ctx, description='Registration failed. Please try again.', color=discord.Color.red())

@bot.command(name='removeadmin')
@commands.has_permissions(administrator=True)
async def OnRemoveAdmin(ctx, member:discord.Member):
	print('User {0.author} is removing admin permissions from {1}'.format(ctx, member))

	if (botSettings.adminRole is None):
		raise AdminRoleUnitialized()

	try:
		await member.remove_roles(botSettings.adminRole, reason='User {0.author} is removing admin permissions from {1}'.format(ctx, member))
		await SendMessage(ctx, description='You have removed admin permissions from {0.mention}.'.format(member), color=discord.Color.blue())
	except discord.HTTPException:
		await SendMessage(ctx, description='Removal failed. Please try again.', color=discord.Color.red())

@bot.command(name='join', aliases=['j'])
@IsValidChannel(ChannelType.LOBBY)
async def OnJoinQueue(ctx):
	print('User {0.author} is joining queue.'.format(ctx))

	if (matchService.IsPlayerQueued(ctx.author)):
		raise PlayerAlreadyQueued(ctx.author)

	await matchService.JoinQueue(ctx, ctx.author)

@bot.command(name='leave', aliases=['l'])
@IsValidChannel(ChannelType.LOBBY)
async def OnLeaveQueue(ctx):
	print('User {0.author} is leaving queue.'.format(ctx))

	if (not matchService.IsPlayerQueued(ctx.author)):
		raise PlayerNotQueued(ctx.author)

	await matchService.LeaveQueue(ctx, ctx.author)

@bot.command(name='queue')
@IsValidChannel(ChannelType.LOBBY)
async def OnShowQueue(ctx):
	print('Showing queue')

	await matchService.ShowQueue(ctx)

@bot.command(name='forcestartmatch')
@IsValidChannel(ChannelType.LOBBY)
@commands.has_permissions(administrator=True)
async def OnForceStartMatch(ctx):
	print('{} is force starting the match'.format(ctx.author))

	await matchService.StartMatch(ctx)

@bot.command(name='clearchannel')
@commands.has_permissions(administrator=True)
async def OnClearChannel(ctx, channel:discord.TextChannel, channelType:ChannelType):
	print('Channel: {} type: {}'.format(channel, channelType))

	if (channelType is ChannelType.LOBBY):
		botSettings.SetLobbyChannel(None)
	elif (channelType is ChannelType.REGISTER):
		botSettings.SetRegisterChannel(None)
	elif (channelType is ChannelType.ADMIN):
		botSettings.SetAdminChannel(None)
	elif (channelType is ChannelType.RESULTS):
		botSettings.SetResultsChannel(None)

	await SendMessage(ctx, description='{0.mention} has been cleared as the {1.value} channel'.format(channel, channelType), color=discord.Color.blue())

@bot.command(name='setchannel')
@commands.has_permissions(administrator=True)
async def OnSetChannel(ctx, channel:discord.TextChannel, channelType:ChannelType):
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

	await SendMessage(ctx, description='{0.mention} has been set as the {1.value} channel'.format(channel, channelType), color=discord.Color.blue())

@bot.command(name='setregisteredrole')
@commands.has_permissions(administrator=True)
async def OnSetRegisteredRole(ctx, role:discord.Role):
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

@bot.command(name='setadminrole')
@commands.has_permissions(administrator=True)
async def OnSetAdminRole(ctx, role:discord.Role):
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

@bot.command(name='addrank')
@commands.has_permissions(administrator=True)
async def OnAddRank(ctx, role:discord.Role, mmrMin:int, mmrMax:int, mmrDelta:int):
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

@bot.command(name='updaterank')
@commands.has_permissions(administrator=True)
async def OnUpdateRank(ctx, role:discord.Role, mmrMin:int, mmrMax:int, mmrDelta:int):
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

@bot.command(name='removerank')
@commands.has_permissions(administrator=True)
async def OnRemoveRank(ctx, role:discord.Role):
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

	botSettings.RemoveMMRRole(role)
	await SendMessage(ctx, title='Rank Removed', description='Role: {0.mention}\nMMR Range: {1}-{2}\nMMR Delta: +-{3}'.format(role, mmrMin, mmrMax, mmrDelta), color=discord.Color.blue())

@bot.command(name='ranks')
async def OnShowRanks(ctx):
	print('Showing ranks')

	roles = botSettings.GetSortedMMRRoles()
	fields = []

	for role in roles:
		field = {}
		field['name'] = '{0.name}'.format(role.role)
		field['value'] = 'Role: {0.mention}\nMMR Range: {1}-{2}\nMMR Delta: +-{3}'.format(role.role, role.mmrMin, role.mmrMax, role.mmrDelta)
		field['inline'] = False
		fields.append(field)

	if (len(fields) == 0):
		await SendMessage(ctx, description='There are currently no ranks.', color=discord.Color.blue())
	else:
		await SendMessage(ctx, fields=fields, color=discord.Color.blue())

@bot.command(name='setmmr')
@commands.has_permissions(administrator=True)
async def OnSetMMR(ctx, member:discord.Member, mmr:int):
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

@bot.command(name='refreshuser')
@commands.has_permissions(administrator=True)
async def OnRefreshUser(ctx, member:discord.Member):
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

@bot.command(name='refreshusers')
@commands.has_permissions(administrator=True)
async def OnRefreshUsers(ctx):
	print('Refreshing roles on all users')

	if (botSettings.guild is None):
		raise InvalidGuild()

	mmrRoles = botSettings.GetAllMMRRoles()

	if (len(mmrRoles) == 0):
		raise NoMMRRoles()

	for player in botSettings.registeredPlayers.values():
		previousRole, newRole = botSettings.GetMMRRole(player.user)

		member = None
		try:
			member = await botSettings.guild.fetch_member(player.user.id)
		except discord.HTTPException:
			await SendMessage(ctx, description='Failed to find member {0.mention}. Ignoring this user.'.format(player.user), color=discord.Color.gold())

		# Just ignore users who aren't in the guild
		if (member is None):
			continue

		# Remove all their previous mmr roles and readd the correct one
		await RemoveRoles(ctx, member, *mmrRoles, errorMessage='Failed to remove previous rank from {0.mention}. Please try again.'.format(member))
		await AddRoles(ctx, member, newRole.role, botSettings.registeredRole, errorMessage='Failed to add current rank to {0.mention}. Please try again.'.format(member))

	await SendMessage(ctx, description='Ranks have been updated on all registered players.', color=discord.Color.blue())

@bot.command(name='addmap')
@commands.has_permissions(administrator=True)
async def OnAddMap(ctx, name:str):
	print('Adding map: {}'.format(name))

	if (botSettings.DoesMapExist(name)):
		raise MapExists(name)

	botSettings.AddMap(name)
	await SendMessage(ctx, description='`{}` has been added as a map.'.format(name), color=discord.Color.blue())

@bot.command(name='removemap')
@commands.has_permissions(administrator=True)
async def OnRemoveMap(ctx, name:str):
	print('Removing map: {}'.format(name))

	if (not botSettings.DoesMapExist(name)):
		raise InvalidMap(name)

	botSettings.RemoveMap(name)
	await SendMessage(ctx, description='`{}` has been removed as a map.'.format(name), color=discord.Color.blue())

@bot.command(name='maps')
async def OnShowMaps(ctx):
	print('Showing maps')

	maps = botSettings.GetSortedMaps()
	fields = []

	for map in maps:
		field = {}
		field['name'] = '{}'.format(map.name)
		field['value'] = 'Times Played: {}'.format(map.timesPlayed)
		field['inline'] = False
		fields.append(field)

	if (len(fields) == 0):
		await SendMessage(ctx, description='There are currently no maps.', color=discord.Color.blue())
	else:
		await SendMessage(ctx, fields=fields, color=discord.Color.blue())

@bot.command(name='leaderboard')
@commands.has_permissions(administrator=True)
async def OnShowLeaderboards(ctx, page:int=1):
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

@bot.command('recallmatch')
@commands.has_permissions(administrator=True)
async def OnRecallMatch(ctx, matchID:int, newResult:MatchResult):
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
		member = None
		try:
			member = await botSettings.guild.fetch_member(player)
		except discord.HTTPException:
			await SendMessage(ctx, description='Failed to find member {}. Ignoring this user.'.format(player), color=discord.Color.gold())

		# Just ignore users who aren't in the guild
		if (member is None):
			continue

		previousRole, newRole = botSettings.GetMMRRoleByID(player)

		# Remove all their previous mmr roles and readd the correct one
		await RemoveRoles(ctx, member, *mmrRoles, errorMessage='Failed to remove previous rank from {0.mention}. Please try again.'.format(member))
		await AddRoles(ctx, member, newRole.role, botSettings.registeredRole, errorMessage='Failed to add current rank to {0.mention}. Please try again.'.format(member))

	await SendChannelMessage(botSettings.adminChannel, description='The ranks of all players in match #{} have been updated.'.format(match._matchUniqueID), color=discord.Color.blue())

@OnSetChannel.error
@OnClearChannel.error
@OnRegisterPlayer.error
@OnSetName.error
@OnSetRegisteredRole.error
@OnRegisterAdmin.error
@OnRemoveAdmin.error
@OnSetAdminRole.error
@OnJoinQueue.error
@OnLeaveQueue.error
@OnShowQueue.error
@OnRegisterPlayer.error
@OnAddRank.error
@OnUpdateRank.error
@OnRemoveRank.error
@OnShowRanks.error
@OnAddMap.error
@OnRemoveMap.error
@OnSetMMR.error
@OnRefreshUser.error
@OnRefreshUsers.error
@OnForceStartMatch.error
@OnShowLeaderboards.error
@OnRecallMatch.error
async def errorHandling(ctx, error):
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

	elif (isinstance(error, commands.errors.MissingRequiredArgument)):
		await SendMessage(ctx, description='Invalid usage: `{0.name}` is a required argument'.format(error.param), color=discord.Color.red())

	elif (isinstance(error, commands.BadArgument)):
		await SendMessage(ctx, description='Bad Argument: {}'.format(error), color=discord.Color.red())

