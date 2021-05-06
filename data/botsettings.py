from data.playerdata import PlayerData
from data.mmrrole import MMRRole 
from data.matchhistorydata import MatchHistoryData
from enum import Enum

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

        if tempArg.__contains__(ChannelType.LOBBY.value):
            returnType = ChannelType.LOBBY
        elif tempArg.__contains__(ChannelType.RESULTS.value):
            returnType = ChannelType.RESULTS
        elif tempArg.__contains__(ChannelType.REPORT.value):
            returnType = ChannelType.REPORT
        elif tempArg.__contains__(ChannelType.REGISTER.value):
            returnType = ChannelType.REGISTER

        return returnType

class BotSettings(object):
    def __init(self):
        # Channels used for various bot functionality
        # Type: discord.TextChannel
        self.lobbyChannel = None
        self.resultsChannel = None
        self.reportChannel = None
        self.registerChannel = None

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

