from mongoengine import Document, IntField, StringField
from discord.ext import commands

class MapExists(commands.BadArgument):
	def __init__(self, argument):
		self.argument = argument
		super().__init__('{}" is already a map.'.format(argument))

class InvalidMap(commands.BadArgument):
	def __init__(self, argument):
		self.argument = argument
		super().__init__('{}" is not a valid map.'.format(argument))

class SiegeMap(Document):
	# Database fields.  Dont modify or access directly, use the non underscore versions
	_timesPlayed = IntField(default=0)
	_name = StringField(default='')

	# Settings
	timesPlayed = 0
	name = ''

	def __eq__(self, other):
		return self.name.lower == other.name.lower

	def Init(self):
		self.timesPlayed = self._timesPlayed
		self.name = self._name

	def SetName(self, name:str):
		self.name = name
		self._name = name
		self.save()

	def IncrementTimesPlayed(self):
		self.timesPlayed += 1
		self._timesPlayed = self.timesPlayed
		self.save()
