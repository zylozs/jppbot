from mongoengine import Document, IntField, StringField
from discord.ext import commands

class MapExists(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('{}" is already a map.'.format(argument))

class CantRerollMap(commands.BadArgument):
    def __init__(self):
        super().__init__("You can't reroll a map when a match is not in progress.")

class InvalidMap(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('{}" is not a valid map.'.format(argument))

class SiegeMap(Document):
    # Database fields.  Dont modify or access directly, use the non underscore versions
    _timesPlayed = IntField(default=0)
    _name = StringField(default='')
    _thumbnailURL = StringField(default='')

    # Settings
    timesPlayed = 0
    name = ''
    thumbnailURL = ''

    def __eq__(self, other):
        return self.name.lower == other.name.lower

    def Init(self):
        self.timesPlayed = self._timesPlayed
        self.name = self._name
        self.thumbnailURL = self._thumbnailURL

    def SetName(self, name:str, url:str):
        self.name = name
        self._name = name
        self.thumbnailURL = url 
        self._thumbnailURL = url 
        self.save()

    def SetThumbnail(self, url:str):
        self.thumbnailURL = url 
        self._thumbnailURL = url 
        self.save()

    def IncrementTimesPlayed(self):
        self.timesPlayed += 1
        self._timesPlayed = self.timesPlayed
        self.save()
