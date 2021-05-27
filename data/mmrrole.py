from mongoengine import Document, IntField 
import discord
from discord.ext import commands

class InvalidMMRRole(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('Role {0.mention}" is not a valid MMR Role.'.format(argument))

class MMRRoleRangeConflict(commands.BadArgument):
    def __init__(self):
        super().__init__('MMR Role range conflicts with another MMR Role\'s range.')

class MMRRoleExists(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('Role {0.mention}" is already an MMR Role.'.format(argument))

class NoMMRRoles(commands.BadArgument):
    def __init__(self):
        super().__init__('There are no MMR Roles.')

class MMRRole(Document):
    # Database fields.  Dont modify or access directly, use the non underscore versions
    _mmrMin = IntField(default=0)
    _mmrMax = IntField(default=0)
    _mmrDelta = IntField(default=0)
    _role = IntField(default=-1)

    # Settings
    mmrMin = 0 # Inclusive
    mmrMax = 0 # Inclusive
    mmrDelta = 0 # How much to increase/decrease the MMR per match played
    role = None # discord.Role

    def Init(self, guild:discord.Guild):
        self.mmrMin = self._mmrMin
        self.mmrMax = self._mmrMax
        self.mmrDelta = self._mmrDelta
        self.role = guild.get_role(self._role)

    def SetData(self, role:discord.Role, mmrMin:int, mmrMax:int, mmrDelta:int):
        self.mmrMin = mmrMin
        self.mmrMax = mmrMax
        self.mmrDelta = mmrDelta
        self.role = role

        self._mmrMin = mmrMin
        self._mmrMax = mmrMax
        self._mmrDelta = mmrDelta
        self._role = role.id
        self.save()

    def UpdateData(self, mmrMin:int, mmrMax:int, mmrDelta:int):
        self.mmrMin = mmrMin
        self.mmrMax = mmrMax
        self.mmrDelta = mmrDelta

        self._mmrMin = mmrMin
        self._mmrMax = mmrMax
        self._mmrDelta = mmrDelta
        self.save()
