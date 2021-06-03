from mongoengine import Document, IntField, StringField
from services.matchservice import TeamResult
import discord
from discord.ext import commands

class UserNotRegistered(commands.BadArgument):
	def __init__(self, argument):
		self.argument = argument
		super().__init__('User {0.mention}" is not registered.'.format(argument))

class UserAlreadyRegistered(commands.BadArgument):
	def __init__(self, argument):
		self.argument = argument
		super().__init__('User {0.mention}" is already registered.'.format(argument))

class PlayerData(Document):
	# Database fields.  Dont modify or access directly, use the non underscore versions
	_mmr = IntField(default=0)
	_lowestMMR = IntField(default=-1)
	_highestMMR = IntField(default=-1)
	_matchesPlayed = IntField(default=0)
	_wins = IntField(default=0)
	_loses = IntField(default=0)
	_winStreak = IntField(default=0)
	_loseStreak = IntField(default=0)
	_highestWinStreak = IntField(default=0)
	_highestLoseStreak = IntField(default=0)
	_name = StringField(default='')
	_user = IntField(default=-1)

	# Settings
	mmr = 0
	lowestMMR = -1
	highestMMR = -1
	matchesPlayed = 0
	wins = 0
	loses = 0
	winStreak = 0
	loseStreak = 0
	highestWinStreak = 0
	highestLoseStreak = 0
	name = '' # The name choosen by the user when registering
	user = None # discord.User

	async def Init(self, bot):
		self.mmr = self._mmr
		self.lowestMMR = self._lowestMMR
		self.highestMMR = self._highestMMR
		self.winStreak = self._winStreak
		self.loseStreak = self._loseStreak
		self.highestWinStreak = self._highestWinStreak
		self.highestLoseStreak = self._highestLoseStreak
		self.matchesPlayed = self._matchesPlayed
		self.wins = self._wins
		self.loses = self._loses
		self.name = self._name
		self.user = bot.get_user(self._user)

	def RedoData(self, oldDelta:int, mmrDelta:int, prevResult:TeamResult, newResult:TeamResult):
		# undo the previous match
		if (prevResult == TeamResult.WIN):
			self.wins -= 1
			self.mmr -= oldDelta
			self.matchesPlayed -= 1
		elif (prevResult == TeamResult.LOSE):
			self.loses -= 1
			self.mmr += oldDelta
			self.matchesPlayed -= 1

		# Clamp before changing the results to keep results consistent if the user hit something below 0 from this
		self.mmr = max(self.mmr, 0)

		if (newResult == TeamResult.WIN):
			self.wins += 1
			self.mmr += mmrDelta
			self.matchesPlayed += 1
		elif (newResult == TeamResult.LOSE):
			self.loses += 1
			self.mmr -= mmrDelta
			self.matchesPlayed += 1

		# Clamp the mmr so its not possible to go below 0
		self.mmr = max(self.mmr, 0)

		if (self.lowestMMR == -1):
			self.lowestMMR = self.mmr

		if (self.highestMMR == -1):
			self.highestMMR = self.mmr

		self.lowestMMR = min(self.lowestMMR, self.mmr)
		self.highestMMR = max(self.highestMMR, self.mmr)

		# Update database
		self._mmr = self.mmr
		self._lowestMMR = self.lowestMMR
		self._highestMMR = self.highestMMR
		self._wins = self.wins
		self._loses = self.loses
		self._matchesPlayed = self.matchesPlayed
		self.save()

	def UpdateData(self, mmrDelta:int, isWin:bool):
		# Update cache

		if (isWin):
			self.wins += 1
			self.mmr += mmrDelta
			self.highestLoseStreak = max(self.highestLoseStreak, self.loseStreak)
			self.loseStreak = 0
			self.winStreak += 1
			self.highestWinStreak = max(self.highestWinStreak, self.winStreak)
		else:
			self.loses += 1
			self.mmr -= mmrDelta
			self.highestWinStreak = max(self.highestWinStreak, self.winStreak)
			self.winStreak = 0
			self.loseStreak += 1
			self.highestLoseStreak = max(self.highestLoseStreak, self.loseStreak)

		# Clamp the mmr so its not possible to go below 0
		self.mmr = max(self.mmr, 0)

		if (self.lowestMMR == -1):
			self.lowestMMR = self.mmr

		if (self.highestMMR == -1):
			self.highestMMR = self.mmr

		self.lowestMMR = min(self.lowestMMR, self.mmr)
		self.highestMMR = max(self.highestMMR, self.mmr)

		self.matchesPlayed += 1

		# Update database
		self._mmr = self.mmr
		self._lowestMMR = self.lowestMMR
		self._highestMMR = self.highestMMR
		self._wins = self.wins
		self._loses = self.loses
		self._winStreak = self.winStreak
		self._loseStreak = self.loseStreak
		self._highestWinStreak = self.highestWinStreak
		self._highestLoseStreak = self.highestLoseStreak
		self._matchesPlayed = self.matchesPlayed
		self.save()
	
	def SetUser(self, user:discord.User, name:str):
		self.user = user
		self._user = user.id
		self.name = name
		self._name = name
		self.save()

	def SetName(self, name:str):
		self.name = name
		self._name = name
		self.save()

	def SetMMR(self, mmr:int):
		self.mmr = mmr

		if (self.lowestMMR == -1):
			self.lowestMMR = self.mmr

		if (self.highestMMR == -1):
			self.highestMMR = self.mmr

		self.lowestMMR = min(self.lowestMMR, self.mmr)
		self.highestMMR = max(self.highestMMR, self.mmr)

		self._mmr = mmr
		self._lowestMMR = self.lowestMMR
		self._highestMMR = self.highestMMR
		self.save()


