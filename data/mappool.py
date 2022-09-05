from mongoengine import Document, StringField, ListField, IntField
from discord.ext import commands
from enum import Enum

class MapPoolExists(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('`{}` is already a map pool.'.format(argument))

class InvalidMapPool(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('`{}` is not a valid map pool.'.format(argument))

class CantForceMapPool(commands.BadArgument):
    def __init__(self):
        super().__init__("Cant't force a map pool when a match isn't running")

class MapPoolMapExists(commands.BadArgument):
    def __init__(self, argument, argument2):
        self.argument = argument
        self.argument2 = argument2
        super().__init__('`{}` is already a map in `{}`.'.format(argument2, argument))

class InvalidMapPoolMap(commands.BadArgument):
    def __init__(self, argument, argument2):
        self.argument = argument
        self.argument2 = argument2
        super().__init__('`{}` is not a valid map in `{}`.'.format(argument2, argument))

class InvalidMapPoolType(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('Map Pool Type `{}` is not valid.'.format(argument))

class MapPoolType(Enum):
    ALL = 0
    CUSTOM = 1
    EXCLUDE = 2
    INVALID = 3

    @classmethod
    async def convert(cls, ctx, argument):
        returnType = MapPoolType.INVALID

        if (isinstance(argument, int) or argument.isnumeric()):
            tempArg = int(argument)
            if (tempArg == MapPoolType.ALL.value):
                returnType = MapPoolType.ALL
            elif (tempArg == MapPoolType.CUSTOM.value):
                returnType = MapPoolType.CUSTOM
            elif (tempArg == MapPoolType.EXCLUDE.value):
                returnType = MapPoolType.EXCLUDE
        elif (isinstance(argument, str)):
            tempArg = argument.lower()
            if (tempArg.__contains__('all') or tempArg == 'a'):
                returnType = MapPoolType.ALL
            elif (tempArg.__contains__('custom') or tempArg == 'c'):
                returnType = MapPoolType.CUSTOM
            elif (tempArg.__contains__('exclude') or tempArg == 'e'):
                returnType = MapPoolType.EXCLUDE

        if (returnType is MapPoolType.INVALID):
            raise InvalidMapPoolType(argument)
        else:
            return returnType

class MapPool(Document):
    # Database fields.  Dont modify or access directly, use the non underscore versions
    _name = StringField(default='')
    _timesPlayed = IntField(default=0)
    _maps = ListField(StringField())
    _type = IntField(default=0)

    # Types
    # 0 = All Maps
    # 1 = Custom Map List
    # 2 = All maps excluding specified

    # Settings
    name = ''
    timesPlayed = 0
    maps = []
    type = 0

    def __eq__(self, other):
        return self.name.lower == other.name.lower

    def Init(self):
        self.name = self._name
        self.timesPlayed = self._timesPlayed
        self.maps = []
        self.type = self._type

        for map in self._maps:
            self.maps.append(map)

    def SetData(self, name:str, type:int):
        self.name = name
        self.type = type
        self.timesPlayed = 0
        self.maps = []

        self._name = name
        self._type = type
        self._timesPlayed = 0
        self._maps = []
        self.save()

    def SetName(self, name:str):
        self.name = name
        self._name = name
        self.save()

    def SetType(self, type:int):
        self.type = type
        self._type = type
        self.save()

    def IncrementTimesPlayed(self):
        self.timesPlayed += 1
        self._timesPlayed = self.timesPlayed
        self.save()

    def AddMap(self, map:str):
        self.maps.append(map)
        self._maps.append(map)
        self.save()

    def RemoveMap(self, map:str):
        if (map in self.maps):
            self.maps.remove(map)
        if (map in self._maps):
            self._maps.remove(map)
        self.save()

    def GetMapNames(self):
        if (self.type == MapPoolType.ALL.value):
            return 'All'

        if len(self.maps) == 0:
            return 'None'

        names = ''
        for _map in self.maps:
            names += _map + ', '

        return names[:-2]

    def IsValidMap(self, map:str):
        if (self.type == MapPoolType.CUSTOM.value):
            return map in self.maps
        elif (self.type == MapPoolType.EXCLUDE.value):
            return map not in self.maps

        return True 
