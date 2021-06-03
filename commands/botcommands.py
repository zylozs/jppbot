from data.botsettings import ChannelType, RegisteredRoleUnitialized, InvalidGuild, EmptyName
from data.playerdata import UserNotRegistered, UserAlreadyRegistered
from data.matchhistorydata import MatchHistoryData, MatchResult
from services.matchservice import PlayerAlreadyQueued, PlayerNotQueued
from utils.chatutils import SendMessage
from utils.botutils import IsValidChannel
from utils.errorutils import HandleError
from globals import *
from discord.ext import commands
import discord
import random

class BotCommands(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_message(self, message):
		if message.author.bot:
			return

		if message.author.id == 86642208693825536 and message.guild is None and message.content.startswith('!setnickname'):
			member = botSettings.guild.get_member(self.bot.user.id)
			content = message.content.split(' ', 1)

			if (len(content) > 1):
				newNickname = content[1]
				await member.edit(nick=newNickname)
				print('Changing nickname to: {}'.format(newNickname))
			return

		if message.guild is None:
			return

		if not message.mention_everyone and self.bot.user.mentioned_in(message):
			quips = ['Bonjour', str(discord.utils.get(message.guild.emojis, name='jpp')), 'yolo', 'Sorry, im playing Apex', ':sunglasses:', 'Beat Saber :heart:', 'We as a team', 'https://tenor.com/view/this-is-fine-fire-house-burning-okay-gif-5263684', 'Villa is the best']

			# pmcc detected
			if message.author.id == 90342358620573696:
				quips.extend(['Are you my twin?', 'Seems pretty sus'])

			await message.channel.send(random.choice(quips))
		elif 'jpp' in message.content.lower() and not message.content.startswith('!jpp'):
			await message.add_reaction(str(discord.utils.get(message.guild.emojis, name='jpp')))
		elif '👀' in message.content:
			await message.add_reaction('👀')
		elif 'golf' in message.content.lower() and not message.content.startswith('!golfit'):
			await message.add_reaction('⛳')

	@commands.Cog.listener()
	async def on_ready(self):
		print('We have logged in as {0.user}'.format(self.bot))
		await botSettings.InitSettings(self.bot)

	@commands.command(name='jpp')
	async def OnJPP(self, ctx):
		"""jpp"""

		emoji = discord.utils.get(ctx.guild.emojis, name='jpp')
		await ctx.send(str(emoji))

	@commands.command(name='golfit')
	async def OnGolfIt(self, ctx):
		"""For all your golf it music needs"""
		await ctx.send('https://www.youtube.com/watch?v=KtmGzvBjAYU')

	@commands.command(name='whendoesbeauloplay')
	async def OnWhenDoesBeauloPlay(self, ctx):
		"""👀"""
		await ctx.send(':eyes: https://www.twitch.tv/beaulo')
	
	@commands.command(name='register', aliases=['r'], brief='Allows a user to register with the bot')
	@IsValidChannel(ChannelType.REGISTER)
	async def OnRegisterPlayer(self, ctx, *name):
		"""Allows a user to register with the bot. This enables matchmaking functionality for that user.

		   **string:** <name>
		   The name you want to use with the bot. Spaces and special characters are allowed.
		"""
		if (len(name) == 0):
			raise EmptyName()

		combinedName = ' '.join(name)
		print('User {0.author} is registering with name {1}'.format(ctx, combinedName))
	
		if (botSettings.registeredRole is None):
			raise RegisteredRoleUnitialized()

		if (botSettings.IsUserRegistered(ctx.author)):
			raise UserAlreadyRegistered(ctx.author)

		try:
			await ctx.author.add_roles(botSettings.registeredRole, reason='User {0.name} used the register command'.format(ctx.author))

			botSettings.RegisterUser(ctx.author, combinedName)

			await SendMessage(ctx, description='You have been registered as `{}`!'.format(combinedName), color=discord.Color.blue())
		except discord.HTTPException:
			await SendMessage(ctx, description='Registration failed. Please try again.', color=discord.Color.red())

	@commands.command(name='setname')
	async def OnSetName(self, ctx, *name):
		"""Change your name with the bot
		
		   **string:** <name>
		   The name you want to use with the bot. Spaces and special characters are allowed.
		"""
		if (len(name) == 0):
			raise EmptyName()

		combinedName = ' '.join(name)
		print('User {0.author} is changing their name to {1}'.format(ctx, combinedName))

		if (not botSettings.IsUserRegistered(ctx.author)):
			raise UserNotRegistered(ctx.author)

		botSettings.ChangeName(ctx.author, combinedName)

		await SendMessage(ctx, description='Your name has been changed to `{}`'.format(combinedName), color=discord.Color.blue())

	@commands.command(name='join', aliases=['j'])
	@IsValidChannel(ChannelType.LOBBY)
	async def OnJoinQueue(self, ctx):
		"""Join the matchmaking queue"""
		print('User {0.author} is joining queue.'.format(ctx))

		if (not botSettings.IsUserRegistered(ctx.author)):
			raise UserNotRegistered(ctx.author)

		if (matchService.IsPlayerQueued(ctx.author)):
			raise PlayerAlreadyQueued(ctx.author)

		await matchService.JoinQueue(ctx, ctx.author)

	@commands.command(name='leave', aliases=['l'])
	@IsValidChannel(ChannelType.LOBBY)
	async def OnLeaveQueue(self, ctx):
		"""Leave the matchmaking queue"""
		print('User {0.author} is leaving queue.'.format(ctx))

		if (not botSettings.IsUserRegistered(ctx.author)):
			raise UserNotRegistered(ctx.author)

		if (not matchService.IsPlayerQueued(ctx.author)):
			raise PlayerNotQueued(ctx.author)

		await matchService.LeaveQueue(ctx, ctx.author)

	@commands.command(name='queue')
	@IsValidChannel(ChannelType.LOBBY)
	async def OnShowQueue(self, ctx):
		"""Show the matchmaking queue"""
		print('Showing queue')

		await matchService.ShowQueue(ctx)

	@commands.command(name='missing')
	@IsValidChannel(ChannelType.LOBBY)
	async def OnShowMissingPlayers(self, ctx):
		"""Shows who is not in the matchmaking queue"""
		print('Showing missing players')

		if (botSettings.guild is None):
			raise InvalidGuild()

		missingMembers = []
		for channel in botSettings.guild.voice_channels:
			missingMembers.extend(matchService.GetNotInQueue(channel.members))

		if (len(missingMembers) == 0):
			await SendMessage(ctx, description='Nobody is missing from queue.', color=discord.Color.blue())
			return

		field = {}
		field['name'] = 'Players not in queue'
		field['value'] = ''
		field['inline'] = False

		isFirst = True

		for member in missingMembers:
			if (isFirst):
				isFirst = False
			else:
				description += '\n'

			field['value'] += '{0.mention}\n'.format(member)

		await SendMessage(ctx, fields=[field], color=discord.Color.blue())

	@commands.command(name='ranks')
	async def OnShowRanks(self, ctx):
		"""Shows the ranks"""
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

	@commands.command(name='maps')
	async def OnShowMaps(self, ctx):
		"""Shows the maps"""
		print('Showing maps')

		maps = botSettings.GetSortedMaps()
		fields = []

		for _map in maps:
			field = {}
			field['name'] = '{}'.format(_map.name)
			field['value'] = 'Times Played: {}'.format(_map.timesPlayed)
			field['inline'] = True 
			fields.append(field)

		numMaps = len(maps)
		footer = '{} map{}'.format(numMaps, '' if numMaps == 1 else 's')

		if (len(fields) == 0):
			await SendMessage(ctx, description='There are currently no maps.', color=discord.Color.blue())
		else:
			await SendMessage(ctx, fields=fields, footer=footer, color=discord.Color.blue())

	@commands.command(name='stats')
	async def OnShowStats(self, ctx):
		"""Shows your stats"""
		print('Showing stats for {}'.format(ctx.author))

		if (not botSettings.IsUserRegistered(ctx.author)):
			raise UserNotRegistered(ctx.author)

		player = botSettings.GetRegisteredPlayerByID(ctx.author.id)
		prevRole, currentRole = botSettings.GetMMRRole(ctx.author)

		results = {}

		def AddWin(map:str):
			if (map not in results):
				results[map] = [1, 0, map]
			else:
				results[map][0] += 1

		def AddLoss(map:str):
			if (map not in results):
				results[map] = [0, 1, map]
			else:
				results[map][1] += 1

		team1Matches = MatchHistoryData.objects(_team1__match={'_id':ctx.author.id}) 
		team2Matches = MatchHistoryData.objects(_team2__match={'_id':ctx.author.id})

		def CheckResults(matches, winResult, loseResult):
			for data in matches:
				if (data._result == MatchResult.CANCELLED.value):
					continue

				if (data._result == winResult):
					AddWin(data._map)
				elif (data._result == loseResult):
					AddLoss(data._map)

		CheckResults(team1Matches, MatchResult.TEAM1VICTORY.value, MatchResult.TEAM2VICTORY.value)
		CheckResults(team2Matches, MatchResult.TEAM2VICTORY.value, MatchResult.TEAM1VICTORY.value)
	
		bestMaps = sorted(results.values(), key=lambda map : map[0], reverse=True)
		worstMaps = sorted(results.values(), key=lambda map : map[1], reverse=True)

		bestMap = bestMaps[0] if len(bestMaps) > 0 else None
		worstMap = worstMaps[0] if len(worstMaps) > 0 else None

		winLossDelta = player.wins - player.loses
		winLossPercent = player.wins / (1 if player.matchesPlayed == 0 else player.matchesPlayed)
		wlDelta = '{}{}'.format('+' if winLossDelta >= 0 else '-', abs(winLossDelta))

		title = 'Stats for {}'.format(player.name)
		description = '**Rank:** {0.mention}\n'.format(currentRole.role)
		description += '**MMR:** {}\n'.format(player.mmr)
		description += '**Highest/Lowest:** {}/{}\n'.format(player.highestMMR, player.lowestMMR)
		description += '**Matches Played:** {}\n'.format(player.matchesPlayed)
		description += '**Win/Loss:** {}/{} ({}, {:.2f}%)\n'.format(player.wins, player.loses, wlDelta, winLossPercent * 100)

		if (bestMap is not None):
			bestMapDelta = bestMap[0] - bestMap[1]
			numPlayed = bestMap[0] + bestMap[1]
			bestMapWinLossPercent = bestMap[0] / (1 if numPlayed == 0 else numPlayed)
			bmDelta = '{}{}'.format('+' if bestMapDelta >= 0 else '-', abs(bestMapDelta))
			description += '**Best Map:** {} ({}, {:.2f}%)\n'.format(bestMap[2], bmDelta, bestMapWinLossPercent * 100)

		if (worstMap is not None):
			worstMapDelta = worstMap[0] - worstMap[1]
			numPlayed = worstMap[0] + worstMap[1]
			worstMapWinLossPercent = worstMap[0] / (1 if numPlayed == 0 else numPlayed)
			wmDelta = '{}{}'.format('+' if worstMapDelta >= 0 else '-', abs(worstMapDelta))
			description += '**Worst Map:** {} ({}, {:.2f}%)'.format(worstMap[2], wmDelta, worstMapWinLossPercent * 100)

		await SendMessage(ctx, title=title, description=description, color=discord.Color.blue())

	@OnJPP.error
	@OnWhenDoesBeauloPlay.error
	@OnRegisterPlayer.error
	@OnSetName.error
	@OnJoinQueue.error
	@OnLeaveQueue.error
	@OnShowQueue.error
	@OnShowMissingPlayers.error
	@OnShowRanks.error
	@OnShowMaps.error
	@OnShowStats.error
	@OnGolfIt.error
	async def errorHandling(self, ctx, error):
		await HandleError(ctx, error)
