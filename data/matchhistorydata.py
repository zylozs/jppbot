from enum import Enum
from discord.ext import commands

class InvalidMatchResult(commands.BadArgument):
	def __init__(self, argument):
		self.argument = argument
		super().__init__('Match Result "{}" is not valid.'.format(argument))

class MatchResult(Enum):
	TEAM1VICTORY = 0
	TEAM2VICTORY = 1
	CANCELLED = 2
	INVALID = 3

	@classmethod
	async def convert(cls, ctx, argument):
		tempArg = argument.lower()
		returnType = MatchResult.INVALID

		if (tempArg.__contains__(MatchResult.TEAM1VICTORY.value)):
			returnType = MatchResult.TEAM1VICTORY
		elif (tempArg.__contains__(MatchResult.TEAM2VICTORY.value)):
			returnType = MatchResult.TEAM2VICTORY
		elif (tempArg.__contains__(MatchResult.CANCELLED.value)):
			returnType = MatchResult.CANCELLED

		if (returnType is MatchResult.INVALID):
			raise InvalidMatchResult(argument)
		else:
			return returnType

class MatchHistoryData(object):
	def __init__(self):
		self.team1 = [] # Array<PlayerData>
		self.team2 = [] # Array<PlayerData>
		self.result = None # MatchResult
		self.map = ""
		self.creationTime = None # datetime.datetime
		self.matchNumber = 0
