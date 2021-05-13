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

class ChannelType(Enum):
    LOBBY = "lobby"
    RESULTS = "result"
    REPORT = "report"
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
        elif (tempArg.__contains__(ChannelType.REPORT.value)):
            returnType = ChannelType.REPORT
        elif (tempArg.__contains__(ChannelType.REGISTER.value)):
            returnType = ChannelType.REGISTER

        if (returnType is ChannelType.INVALID):
            raise ChannelTypeInvalid(argument)
        else:
            return returnType

class BotSettings(Document):
    # Database fields.  Dont modify or access directly, use the non underscore
    # versions
    _lobbyChannel = IntField(default=-1)
    _resultsChannel = IntField(default=-1)
    _reportChannel = IntField(default=-1) 
    _registerChannel = IntField(default=-1)

    def _GetChannel(self, id, bot):
        if (len(bot.guilds) == 0):
            return None

        # This bot is only intended to work in one guild, just grab the first
        guild = bot.guilds[0]

        if (guild and id is not -1):
            return guild.get_channel(id)

        return None

    def InitSettings(self, bot):
        # Channels used for various bot functionality
        # Type: discord.TextChannel
        self.lobbyChannel = self._GetChannel(self._lobbyChannel, bot)
        self.resultsChannel = self._GetChannel(self._resultsChannel, bot)
        self.reportChannel = self._GetChannel(self._reportChannel, bot)
        self.registerChannel = self._GetChannel(self._registerChannel, bot)

        # Player data
        # Type: Dictionary<key=discord.User, value=PlayerData>
        self.registeredPlayers = {}
        self.registeredRole = None # discord.Role

        # MMR Rank definition
        # Type: Array<MMRRole>
        self.mmrRoles = []

        # Historical match data
        # Type: Array<MatchHistoryData>
        self.matchHistory = []

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
            raise commands.BadArgument("Argument [channel] is not None or a valid Discord TextChannel")

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
            raise commands.BadArgument("Argument [channel] is not None or a valid Discord TextChannel")

    # channel: Union[None, discord.TextChannel]
    def SetReportChannel(self, channel):
        if (channel is None):
            self.reportChannel = None
            self._reportChannel = -1
            self.save()
        elif (isinstance(channel, discord.TextChannel)):
            self.reportChannel = channel
            self._reportChannel = channel.id
            self.save()
        else:
            raise commands.BadArgument("Argument [channel] is not None or a valid Discord TextChannel")

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
            raise commands.BadArgument("Argument [channel] is not None or a valid Discord TextChannel")





