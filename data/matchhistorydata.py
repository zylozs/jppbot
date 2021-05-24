from mongoengine import Document, EmbeddedDocument, ListField, IntField, StringField, EmbeddedDocumentField
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

class MatchHistoryPlayerData(EmbeddedDocument):
	# Database fields.  Dont modify or access directly, use the non underscore versions
	_id = IntField(default=0)
	_prevMMR = IntField(default=0)
	_newMMR = IntField(default=0)
	_mmrDelta = IntField(default=0)

class MatchHistoryData(Document):
	# Database fields.  Dont modify or access directly, use the non underscore versions
	_winningTeam = ListField(EmbeddedDocumentField(MatchHistoryPlayerData), max_length=5)
	_losingTeam = ListField(EmbeddedDocumentField(MatchHistoryPlayerData), max_length=5)
	_result = IntField(default=MatchResult.INVALID.value)
	_map = StringField(default='')
	_creationTime = StringField(default='')
	_matchUniqueID = IntField(default=0)

	def StoreData(self, winningTeam, losingTeam, result:MatchResult, selectedMap:str, creationTime:str, id:int):
		self._winningTeam = winningTeam 
		self._losingTeam = losingTeam 
		self._result = result.value
		self._map = selectedMap
		self._creationTime = creationTime
		self._matchUniqueID = id
		self.save()
