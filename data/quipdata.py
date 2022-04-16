from mongoengine import Document, IntField, StringField
from enum import Enum
from discord.ext import commands
import discord

class NoQuips(commands.BadArgument):
    def __init__(self):
        super().__init__('There are no quips yet.')

class InvalidQuipType(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('Quip Type "{}" is not valid.'.format(argument))

class InvalidGuildEmoji(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('"{}" is not a valid guild emoji.'.format(argument))

class QuipType(Enum):
    REGULAR = 0
    GUILD_EMOJI = 1
    SPECIFIC_USER = 2
    INVALID = 3

    @classmethod
    async def convert(cls, ctx, argument):
        returnType = QuipType.INVALID

        if (isinstance(argument, int) or argument.isnumeric()):
            tempArg = int(argument)
            if (tempArg == QuipType.REGULAR.value):
                returnType = QuipType.REGULAR
            elif (tempArg == QuipType.GUILD_EMOJI.value):
                returnType = QuipType.GUILD_EMOJI
            elif (tempArg == QuipType.SPECIFIC_USER.value):
                returnType = QuipType.SPECIFIC_USER
        elif (isinstance(argument, str)):
            tempArg = argument.lower()
            if (tempArg.__contains__('regular') or tempArg == 'r'):
                returnType = QuipType.REGULAR
            elif (tempArg.__contains__('emoji') or tempArg == 'e'):
                returnType = QuipType.GUILD_EMOJI
            elif (tempArg.__contains__('user') or tempArg == 'u'):
                returnType = QuipType.SPECIFIC_USER

        if (returnType is QuipType.INVALID):
            raise InvalidQuipType(argument)
        else:
            return returnType

class QuipData(Document):
    _quip = StringField(default='')
    _type = IntField(default=0)
    _user = IntField(default=-1)
    _useCount = IntField(default=0)

    quip = ''
    type = 0
    user = None # discord.User
    useCount = 0

    def Init(self, bot):
        self.quip = self._quip
        self.type = self._type
        self.user = bot.get_user(self._user)
        self.useCount = self._useCount

    def SetData(self, quip:str, type:int, user):
        self.quip = quip 
        self.type = type  
        self.user = user
        self.useCount = 0

        self._quip = quip 
        self._type = type 
        self._user = user.id if user is not None else None
        self._useCount = 0
        self.save()

    def SetQuip(self, quip:str):
        self.quip = quip 
        self._quip = quip 
        self.save()

    def SetType(self, type:int):
        self.type = type  
        self._type = type 
        self.save()

    def SetUser(self, user:discord.User):
        self.user = user
        self._user = user.id
        self.save()

    def IncrementUse(self):
        self.useCount += 1
        self._useCount += 1
        self.save()

