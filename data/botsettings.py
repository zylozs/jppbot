from data.playerdata import PlayerData
from data.mmrrole import MMRRole 
from data.matchhistorydata import MatchHistoryData
from enum import Enum
from discord.ext import commands
from mongoengine import Document, IntField 
import discord

class ChannelTypeInvalid(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('Channel Type "{}" is not valid.'.format(argument))

class RegisteredRoleUnitialized(commands.CommandError):
    def __init__(self):
        super().__init__('The registered role has not been setup.')

class AdminRoleUnitialized(commands.CommandError):
    def __init__(self):
        super().__init__('The admin role has not been setup.')

class GuildTextChannelMismatch(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('Text Channel "{0.mention}" is not in the same guild as the other text channels.'.format(argument))

class GuildRoleMismatch(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('Role {0.mention}" is not in the same guild as the text channels.'.format(argument))

class ChannelType(Enum):
    LOBBY = "lobby"
    RESULTS = "result"
    ADMIN = "admin"
    REGISTER = "register"
    INVALID = "invalid"

    @classmethod
    async def convert(cls, ctx, argument):
        tempArg = argument.lower()
        returnType = ChannelType.INVALID

        if (tempArg.__contains__(ChannelType.LOBBY.value)):
            returnType = ChannelType.LOBBY
        elif (tempArg.__contains__(ChannelType.RESULTS.value)):
            returnType = ChannelType.RESULTS
        elif (tempArg.__contains__(ChannelType.ADMIN.value)):
            returnType = ChannelType.ADMIN
        elif (tempArg.__contains__(ChannelType.REGISTER.value)):
            returnType = ChannelType.REGISTER

        if (returnType is ChannelType.INVALID):
            raise ChannelTypeInvalid(argument)
        else:
            return returnType

class BotSettings(Document):
    # Database fields.  Dont modify or access directly, use the non underscore
    # versions
    _guild = IntField(default=-1)
    _lobbyChannel = IntField(default=-1)
    _resultsChannel = IntField(default=-1)
    _adminChannel = IntField(default=-1) 
    _registerChannel = IntField(default=-1)
    _registeredRole = IntField(default=-1)
    _adminRole = IntField(default=-1)

    # Settings
    guild = None # discord.Guild
    lobbyChannel = None # discord.TextChannel
    resultsChannel = None # discord.TextChannel
    adminChannel = None # discord.TextChannel
    registerChannel = None # discord.TextChannel
    registeredRole = None # discord.Role
    adminRole = None # discord.Role

    def _GetGuild(self, id, bot):
        if (len(bot.guilds) == 0):
            return None

        return bot.get_guild(id)

    def _GetChannel(self, id):
        if (self.guild is None):
            return None

        # This bot is only intended to work in one guild. Grab the one that matches our guild id
        return self.guild.get_channel(id)

    def _GetRole(self, id):
        if (self.guild is None):
            return None

        return self.guild.get_role(id)

    def InitSettings(self, bot):
        # Channels used for various bot functionality
        # Type: discord.TextChannel
        self.guild = self._GetGuild(self._guild, bot)
        self.lobbyChannel = self._GetChannel(self._lobbyChannel)
        self.resultsChannel = self._GetChannel(self._resultsChannel)
        self.adminChannel = self._GetChannel(self._adminChannel)
        self.registerChannel = self._GetChannel(self._registerChannel)

        # Player data
        # Type: Dictionary<key=discord.User, value=PlayerData>
        self.registeredPlayers = {}
        self.registeredRole = self._GetRole(self._registeredRole)
        self.adminRole = self._GetRole(self._adminRole)

        # MMR Rank definition
        # Type: Array<MMRRole>
        self.mmrRoles = []

        # Historical match data
        # Type: Array<MatchHistoryData>
        self.matchHistory = []
        print('Settings Loaded')

    # channel: Union[None, discord.Guild]
    def SetGuild(self, guild):
        if (guild is None):
            self.guild = None
            self._guild = -1
            self.save()
        elif (isinstance(guild, discord.Guild)):
            self.guild = guild 
            self._guild = guild.id
            self.save()
        else:
            raise commands.BadArgument('Argument [guild] is not None or a valid Discord Guild')

    # channel: Union[None, discord.TextChannel]
    def SetLobbyChannel(self, channel):
        if (channel is None):
            self.lobbyChannel = None
            self._lobbyChannel = -1
            self.save()
        elif (isinstance(channel, discord.TextChannel)):
            self.lobbyChannel = channel
            self._lobbyChannel = channel.id
            self.save()
        else:
            raise commands.BadArgument('Argument [channel] is not None or a valid Discord TextChannel')

    # channel: Union[None, discord.TextChannel]
    def SetResultsChannel(self, channel):
        if (channel is None):
            self.resultsChannel= None
            self._resultsChannel= -1
            self.save()
        elif (isinstance(channel, discord.TextChannel)):
            self.resultsChannel = channel
            self._resultsChannel = channel.id
            self.save()
        else:
            raise commands.BadArgument('Argument [channel] is not None or a valid Discord TextChannel')

    # channel: Union[None, discord.TextChannel]
    def SetAdminChannel(self, channel):
        if (channel is None):
            self.adminChannel = None
            self._adminChannel = -1
            self.save()
        elif (isinstance(channel, discord.TextChannel)):
            self.adminChannel = channel
            self._adminChannel = channel.id
            self.save()
        else:
            raise commands.BadArgument('Argument [channel] is not None or a valid Discord TextChannel')

    # channel: Union[None, discord.TextChannel]
    def SetRegisterChannel(self, channel):
        if (channel is None):
            self.registerChannel = None
            self._registerChannel = -1
            self.save()
        elif (isinstance(channel, discord.TextChannel)):
            self.registerChannel = channel
            self._registerChannel = channel.id
            self.save()
        else:
            raise commands.BadArgument('Argument [channel] is not None or a valid Discord TextChannel')

    # channel: Union[None, discord.Role]
    def SetRegisteredRole(self, role):
        if (role is None):
            self.registeredRole = None
            self._registeredRole = -1
            self.save()
        elif (isinstance(role, discord.Role)):
            self.registeredRole = role 
            self._registeredRole = role.id
            self.save()
        else:
            raise commands.BadArgument('Argument [role] is not None or a valid Discord Role')

    # channel: Union[None, discord.Role]
    def SetAdminRole(self, role):
        if (role is None):
            self.adminRole = None
            self._adminRole = -1
            self.save()
        elif (isinstance(role, discord.Role)):
            self.adminRole = role 
            self._adminRole = role.id
            self.save()
        else:
            raise commands.BadArgument('Argument [role] is not None or a valid Discord Role')

