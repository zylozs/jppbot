import discord
from discord.ext import commands
from utils.chatutils import SendMessage, SendMessageWithFields

class PlayerAlreadyQueued(commands.BadArgument):
	def __init__(self, argument):
		self.argument = argument
		super().__init__('Player {0.mention} is already queued.'.format(argument))

class PlayerNotQueued(commands.BadArgument):
	def __init__(self, argument):
		self.argument = argument
		super().__init__('Player {0.mention} is not currently queued.'.format(argument))

class MatchService(object):
	queuedPlayers = []
	matchesStarted = {}
	botSettings = None

	def Init(self, botSettings):
		self.botSettings = botSettings

	async def JoinQueue(self, ctx, user:discord.User):
		self.queuedPlayers.append(user)

		mmr = self.botSettings.GetMMR(user)

		numPlayers = len(self.queuedPlayers)

		if (numPlayers == 10):
			description = '{0.mention} [{1}] joined the queue.\nThe queue is now full, starting a match...'.format(user, mmr)
		else:
			description = '**[{0}/10]** {1.mention} [{2}] joined the queue.'.format(len(self.queuedPlayers), user, mmr)
		
		await SendMessage(ctx, description=description, color=discord.Color.blue())

		# start the match
		if (numPlayers == 10):
			pass

	async def LeaveQueue(self, ctx, user:discord.User):
		self.queuedPlayers.remove(user)

		mmr = self.botSettings.GetMMR(user)

		numPlayers = len(self.queuedPlayers)

		if (numPlayers == 0):
			description = '{0.mention} [{1}] left the queue.\nThe queue is now empty.'.format(user, mmr)
		else:
			description = '**[{0}/10]** {1.mention} [{2}] left the queue.'.format(numPlayers, user, mmr)

		await SendMessage(ctx, description=description, color=discord.Color.blue())

	async def ShowQueue(self, ctx):
		numPlayers = len(self.queuedPlayers)

		if (numPlayers == 0):
			description = 'The queue is empty.'
			await SendMessage(ctx, description=description, color=discord.Color.blue())
		else:
			title = 'Lobby [{0}/10]'.format(numPlayers)
			description = ''

			for player in self.queuedPlayers:
				mmr = self.botSettings.GetMMR(player)
				description += '[{0}] {1.mention}'.format(mmr, player)

			await SendMessage(ctx, title=title, description=description, color=discord.Color.blue())

	def IsPlayerQueued(self, user:discord.User):
		return user in self.queuedPlayers
