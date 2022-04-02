from mongoengine import Document, IntField, StringField
from enum import Enum
from discord.ext import commands

class InvalidActivityType(commands.BadArgument):
	def __init__(self, argument):
		self.argument = argument
		super().__init__('Activity Type "{}" is not valid.'.format(argument))

class ActivityType(Enum):
	GAME = 0
	WATCHING = 1
	LISTENING = 2
	INVALID = 3

	@classmethod
	async def convert(cls, ctx, argument):
		returnType = ActivityType.INVALID

		if (isinstance(argument, int) or argument.isnumeric()):
			tempArg = int(argument)
			if (tempArg == ActivityType.GAME.value):
				returnType = ActivityType.GAME
			elif (tempArg == ActivityType.WATCHING.value):
				returnType = ActivityType.WATCHING
			elif (tempArg == ActivityType.LISTENING.value):
				returnType = ActivityType.LISTENING
		elif (isinstance(argument, str)):
			tempArg = argument.lower()
			if (tempArg.__contains__('game') or tempArg == 'g'):
				returnType = ActivityType.GAME
			elif (tempArg.__contains__('watch') or tempArg == 'w'):
				returnType = ActivityType.WATCHING
			elif (tempArg.__contains__('listen') or tempArg == 'l'):
				returnType = ActivityType.LISTENING

		if (returnType is ActivityType.INVALID):
			raise InvalidActivityType(argument)
		else:
			return returnType


class ActivityData(Document):
	_name = StringField(default='')
	_type = IntField(default=0)

	# Types
	# 0 = Game Activity
	# 1 = Watching Activity
	# 2 = Listening Activity

	# Settings
	name = ''
	type = 0

	def Init(self):
		self.name = self._name
		self.type = self._type

	def SetData(self, name:str, type:int):
		self.name  = name
		self.type = type

		self._name = name
		self._type = type
		self.save()

	def SetName(self, name:str):
		self.name  = name
		self._name = name
		self.save()

	def SetType(self, type:int):
		self.type = type
		self._type = type
		self.save()
