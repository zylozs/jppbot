import playerdata
import mmrrole

class BotSettings(object):
    """description of class"""

    def __init(self):
        # Channels used for various bot functionality
        # Type: discord.TextChannel
        self.lobbyChannel = None
        self.resultsChannel = None
        self.reportChannel = None
        self.registerChannel = None

        # Player data
        # Type: Dictionary<key=string, value=PlayerData>
        self.registeredPlayers = {}

        # MMR Rank definition
        # Type: Array<MMRRole>
        self.mmrRoles = {}

