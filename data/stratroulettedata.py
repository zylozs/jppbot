from mongoengine import Document, IntField, StringField
from enum import Enum
from discord.ext import commands

class NoStratRouletteStrats(commands.BadArgument):
    def __init__(self):
        super().__init__('There are no strat roulette strats yet.')

class EmptyStrat(commands.BadArgument):
    def __init__(self):
        super().__init__('An empty string is not a valid strat roulette strat.')

class InvalidStratRouletteTeam(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('Strat Roulette Team "{}" is not valid.'.format(argument))

class InvalidStratRouletteTeamType(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('Strat Roulette Team Type "{}" is not valid.'.format(argument))

class StratRouletteTeam(Enum):
    BLUE = 0
    ORANGE = 1
    INVALID = 3

    @classmethod
    async def convert(cls, argument):
        returnType = StratRouletteTeam.INVALID

        if (isinstance(argument, int) or argument.isnumeric()):
            tempArg = int(argument)
            if (tempArg == StratRouletteTeam.BLUE.value):
                returnType = StratRouletteTeam.BLUE
            elif (tempArg == StratRouletteTeam.ORANGE.value):
                returnType = StratRouletteTeam.ORANGE
        elif (isinstance(argument, str)):
            tempArg = argument.lower()
            if (tempArg.__contains__('blue') or tempArg == 'b'):
                returnType = StratRouletteTeam.BLUE
            elif (tempArg.__contains__('orange') or tempArg == 'o'):
                returnType = StratRouletteTeam.ORANGE

        if (returnType is StratRouletteTeam.INVALID):
            raise InvalidStratRouletteTeam(argument)
        else:
            return returnType

class StratRouletteTeamType(Enum):
    ATTACKER = 0
    DEFENDER = 1
    BOTH = 2
    INVALID = 3

    @classmethod
    async def convert(cls, argument):
        returnType = StratRouletteTeamType.INVALID

        if (isinstance(argument, int) or argument.isnumeric()):
            tempArg = int(argument)
            if (tempArg == StratRouletteTeamType.ATTACKER.value):
                returnType = StratRouletteTeamType.ATTACKER
            elif (tempArg == StratRouletteTeamType.DEFENDER.value):
                returnType = StratRouletteTeamType.DEFENDER
            elif (tempArg == StratRouletteTeamType.BOTH.value):
                returnType = StratRouletteTeamType.BOTH
        elif (isinstance(argument, str)):
            tempArg = argument.lower()
            if (tempArg.__contains__('attacker') or tempArg.__contains__('attack') or tempArg == 'a'):
                returnType = StratRouletteTeamType.ATTACKER
            elif (tempArg.__contains__('defender') or tempArg.__contains__('defense') or tempArg == 'd'):
                returnType = StratRouletteTeamType.DEFENDER
            elif (tempArg.__contains__('both') or tempArg == 'b'):
                returnType = StratRouletteTeamType.BOTH

        if (returnType is StratRouletteTeamType.INVALID):
            raise InvalidStratRouletteTeamType(argument)
        else:
            return returnType

class StratRouletteData(Document):
    # Database fields.  Dont modify or access directly, use the non underscore versions
    _timesPlayed = IntField(default=0)
    _title = StringField(default='')
    _strat = StringField(default='')
    _type = IntField(default=0)

    timesPlayed = 0
    title = ''
    strat = ''
    type = 0

    def Init(self):
        self.timesPlayed = self._timesPlayed
        self.title = self._title
        self.strat = self._strat
        self.type = self._type

    def SetData(self, type:int, title:str, strat:str):
        self.title = title
        self.strat = strat
        self.type = type

        self._title = title
        self._strat = strat
        self._type = type
        self.save()

    def SetStrat(self, strat:str):
        self.strat = strat
        self._strat = strat
        self.save()

    def SetTitle(self, title:str):
        self.title = title 
        self._title = title 
        self.save()

    def SetType(self, type:int):
        self.type = type
        self._type = type
        self.save()

    def IncrementTimesPlayed(self):
        self.timesPlayed += 1
        self._timesPlayed += 1
        self.save()

