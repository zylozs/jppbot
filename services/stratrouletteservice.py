import discord
from discord.ext import commands
from data.stratroulettedata import StratRouletteTeam, StratRouletteTeamType
from utils.chatutils import SendMessage

class StratRouletteMatchIsActive(commands.BadArgument):
    def __init__(self):
        super().__init__('There is already an active strat roulette match. Please finish it first before starting a new one.')

class CantStartStratRoulette(commands.BadArgument):
    def __init__(self):
        super().__init__("Can't start Strat Roulette when a match isn't running")

class CantModifyStratRoulette(commands.BadArgument):
    def __init__(self):
        super().__init__("Can't modify the Strat Roulette settings when one isn't running")

class StratRouletteMatch(object):
    team1 = []
    team2 = []
    team1Type = StratRouletteTeamType.INVALID
    team2Type = StratRouletteTeamType.INVALID
    roundNumber = 1
    canTeam1Reroll = True
    canTeam2Reroll = True

    def __init__(self, team1:list[discord.Member], team1Type:StratRouletteTeamType, team2:list[discord.Member], team2Type:StratRouletteTeamType):
        self.team1 = team1
        self.team1Type = team1Type
        self.team2 = team2
        self.team2Type = team2Type

class StratRouletteService(object):
    bot = None
    botSettings = None
    activeMatch = None

    def Init(self, bot, botSettings):
        self.bot = bot
        self.botSettings = botSettings

    async def StartMatch(self, interaction:discord.Interaction, attackers:list[discord.Member], defenders:list[discord.Member]):
        if (self.activeMatch is not None):
            raise StratRouletteMatchIsActive()

        self.activeMatch = StratRouletteMatch(attackers, StratRouletteTeamType.ATTACKER, defenders, StratRouletteTeamType.DEFENDER)

        await SendMessage(interaction, description='_loads revolver_ Let the fun begin!', color=discord.Color.blue())

        # TODO: Send Message to both team channels
        # TODO: Send Message to admin report channel

    async def SetOvertimeRole(self, interaction:discord.Interaction, team:StratRouletteTeam, role:StratRouletteTeamType):
        teamName = 'Blue Team' if team == StratRouletteTeam.BLUE else 'Orange Team'
        roleName = 'Attack' if role == StratRouletteTeamType.ATTACKER else 'Defense'

        await SendMessage(interaction, description='Changing Overtime role for {} to {}'.format(teamName, roleName), color=discord.Color.blue())

    def IsMatchInProgress(self):
        return self.activeMatch is not None