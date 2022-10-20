from mongoengine import Document, IntField, StringField, ListField
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
    _timesRerolled = IntField(default=0)
    _title = StringField(default='')
    _strat = StringField(default='')
    _type = IntField(default=0)

    timesPlayed = 0
    timesRerolled = 0
    title = ''
    strat = ''
    type = 0

    def Init(self):
        self.timesPlayed = self._timesPlayed
        self.timesRerolled = self._timesRerolled
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

    def IncrementTimesRerolled(self):
        self.timesRerolled += 1
        self._timesRerolled += 1
        self.save()

class StratRouletteGlobalMatchData(Document):
    # Database fields.  Dont modify or access directly, use the non underscore versions
    _totalGames = IntField(default=0)
    _totalRerolls = IntField(default=0)
    _totalOvertimes = IntField(default=0)
    _totalOvertimeMistakes = IntField(default=0)

    totalGames = 0
    totalRerolls = 0
    totalOvertimes = 0
    totalOvertimeMistakes = 0

    def Init(self):
        self.totalGames = self._totalGames
        self.totalRerolls = self._totalRerolls
        self.totalOvertimes = self._totalOvertimes
        self.totalOvertimeMistakes = self._totalOvertimeMistakes

    def Increment(self, shouldIncrementGame, totalRerolls:int, overtimeCaller, overtimeFixer):
        if (shouldIncrementGame):
            self.totalGames += 1
            self._totalGames += 1

        self.totalRerolls += totalRerolls 
        self._totalRerolls += totalRerolls 

        if (overtimeCaller is not None):
            self.totalOvertimes += 1
            self._totalOvertimes += 1

        if (overtimeFixer is not None):
            self.totalOvertimeMistakes += 1
            self._totalOvertimeMistakes += 1

        self.save()


class StratRouletteMatchData(Document):
    # Database fields.  Dont modify or access directly, use the non underscore versions
    _matchUniqueID = IntField(default=0)
    _totalRounds = IntField(default=0)
    _team1Rerolls = IntField(default=0)
    _team2Rerolls = IntField(default=0)
    _rerollPlayers = ListField(IntField()) # List of player IDs who rerolled this match. Duplicates are allowed if they rerolled more than once.
    _overtimeCaller = IntField(default=-1) # User.id of person who called the overtime
    _overtimeFixer = IntField(default=-1) # User.id of the admin who had to fix the mess

    def StoreData(self, matchID, totalRounds, team1Rerolls, team2Rerolls, rerollPlayers, overtimeCaller, overtimeFixer):
        self._matchUniqueID = matchID
        self._totalRounds = totalRounds
        self._team1Rerolls = team1Rerolls
        self._team2Rerolls = team2Rerolls
        self._rerollPlayers = rerollPlayers
        self._overtimeCaller = overtimeCaller.id if overtimeCaller is not None else -1
        self._overtimeFixer = overtimeFixer.id if overtimeFixer is not None else -1

        self.save()
