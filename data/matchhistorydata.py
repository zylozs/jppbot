from mongoengine import Document, EmbeddedDocument, ListField, IntField, StringField, EmbeddedDocumentField
from enum import Enum
from discord.ext import commands

class InvalidMatchResult(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('Match Result "{}" is not valid.'.format(argument))

class MatchIDNotFound(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('Match with id `{}` was not found. The match history either doesn\'t exist for this match or this is not a valid match id.'.format(argument))

class MatchResultIdentical(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('`{}` is identical to the current match result'.format(argument))


class MatchResult(Enum):
    TEAM1VICTORY = 0
    TEAM2VICTORY = 1
    CANCELLED = 2
    INVALID = 3

    @classmethod
    async def convert(cls, argument):
        returnType = MatchResult.INVALID

        if (isinstance(argument, int) or argument.isnumeric()):
            tempArg = int(argument)
            if (tempArg == MatchResult.TEAM1VICTORY.value):
                returnType = MatchResult.TEAM1VICTORY
            elif (tempArg == MatchResult.TEAM2VICTORY.value):
                returnType = MatchResult.TEAM2VICTORY
            elif (tempArg == MatchResult.CANCELLED.value):
                returnType = MatchResult.CANCELLED
        elif (isinstance(argument, str)):
            tempArg = argument.lower()
            if (tempArg.__contains__('blue') or tempArg.__contains__('team1') or tempArg == 't1'):
                returnType = MatchResult.TEAM1VICTORY
            elif (tempArg.__contains__('orange') or tempArg.__contains__('team2') or tempArg == 't2'):
                returnType = MatchResult.TEAM2VICTORY
            elif (tempArg.__contains__('cancel')):
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

    def __eq__(self, other):
        if (isinstance(other, int)):
            return self._id == other
        return super().__eq__(other)

class MatchHistoryData(Document):
    # Database fields.  Dont modify or access directly, use the non underscore versions
    _team1 = ListField(EmbeddedDocumentField(MatchHistoryPlayerData), max_length=5)
    _team2 = ListField(EmbeddedDocumentField(MatchHistoryPlayerData), max_length=5)
    _result = IntField(default=MatchResult.INVALID.value)
    _map = StringField(default='')
    _pool = StringField(default='None')
    _creationTime = StringField(default='')
    _matchUniqueID = IntField(default=0)

    def StoreData(self, team1, team2, result:MatchResult, selectedMap:str, pool, creationTime:str, id:int):
        self._team1 = team1 
        self._team2 = team2 
        self._result = result.value
        self._map = selectedMap
        self._pool = 'None' if pool is None else pool
        self._creationTime = creationTime
        self._matchUniqueID = id
        self.save()
