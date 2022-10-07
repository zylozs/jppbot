import discord
from discord.ext import commands
from data.stratroulettedata import StratRouletteTeam, StratRouletteTeamType
from utils.chatutils import EditViewMessage, SendChannelMessage, SendMessage

class StratRouletteMatchIsActive(commands.BadArgument):
    def __init__(self):
        super().__init__('There is already an active strat roulette match. Please finish it first before starting a new one.')

class CantStartStratRoulette(commands.BadArgument):
    def __init__(self):
        super().__init__("Can't start Strat Roulette when a match isn't running")

class CantModifyStratRoulette(commands.BadArgument):
    def __init__(self):
        super().__init__("Can't modify the Strat Roulette settings when one isn't running")

class StratRouletteTeamData(object):
    members = []
    type = StratRouletteTeamType.INVALID
    canReroll = True
    channel = None
    strat = None
    name = ''
    stratMessage = None
    stratView = None

    def __init__(self, _members:list[discord.Member], _type:StratRouletteTeamType, _name:str):
        self.members = _members 
        self.type = _type
        self.name = _name

class StratRouletteStratView(discord.ui.View):
    def __init__(self, botSettings, teamData:StratRouletteTeamData, roundNumber:int):
        # 3 hour timeout by default
        super().__init__(timeout=10800.0)
        self.botSettings = botSettings
        self.team = teamData
        self.roundNumber = roundNumber

    @discord.ui.button(label='Reroll (1)', style=discord.ButtonStyle.green)
    async def RerollStrat(self, interaction:discord.Interaction, button:discord.ui.Button):
        if (interaction.user not in self.team.members):
            await SendMessage(interaction, description='Only members in Team {} can reroll their strat!'.format(self.team.name), color=discord.Color.red(), ephemeral=True)
            return

        if (self.team.canReroll):
            self.team.canReroll = False

            button.label = 'Reroll (0)'
            button.style = discord.ButtonStyle.grey
            button.disabled = True

            self.team.strat = self.botSettings.GetRandomStrat(self.team.type, self.team.strat)

            description = GetTitleFromTeam(self.team)
            field = GetFieldFromTeam(self.roundNumber, self.team)
            await EditViewMessage(interaction, view=self, description=description, fields=[field], color=discord.Color.blue())

        else:
            await SendMessage(interaction, description='Your team has already used up all their rerolls for this round!', color=discord.Color.red(), ephemeral=True)

class StratRouletteMatch(object):
    team1 = None
    team2 = None

    roundNumber = 1

    def __init__(self, team1:list[discord.Member], team1Type:StratRouletteTeamType, team2:list[discord.Member], team2Type:StratRouletteTeamType):
        self.team1 = StratRouletteTeamData(team1, team1Type, 'Blue :blue_square:')
        self.team2 = StratRouletteTeamData(team2, team2Type, 'Orange :orange_square:')

def GetFieldFromTeam(roundNumber:int, team:StratRouletteTeamData):
    field = {}
    field['name'] = 'Round {} Strat'.format(roundNumber)
    field['value'] = '**{}**\n\n{}'.format(team.strat.title, team.strat.strat)
    field['inline'] = False
    return field

def GetTitleFromTeam(team:StratRouletteTeamData):
    description = '**Team {}**\n'.format(team.name)

    for member in team.members:
        if member is not None:
            description += '{0.mention}'.format(member)

    return description

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
        self.activeMatch.team1.strat = self.botSettings.GetRandomStrat(StratRouletteTeamType.ATTACKER)
        self.activeMatch.team2.strat = self.botSettings.GetRandomStrat(StratRouletteTeamType.DEFENDER)

        self.activeMatch.team1.channel = self.botSettings.blueTeamChannel
        self.activeMatch.team2.channel = self.botSettings.orangeTeamChannel

        await self.SendStrat(self.activeMatch.team1)
        await self.SendStrat(self.activeMatch.team2)

    async def SendStrat(self, team:StratRouletteTeamData):
        description = GetTitleFromTeam(team)

        team.stratView = StratRouletteStratView(self.botSettings, team, self.activeMatch.roundNumber)

        field = GetFieldFromTeam(self.activeMatch.roundNumber, team)
        
        team.stratMessage = await SendChannelMessage(team.channel, description=description, fields=[field], color=discord.Color.blue(), view=team.stratView)

    async def SetOvertimeRole(self, interaction:discord.Interaction, team:StratRouletteTeam, role:StratRouletteTeamType):
        teamName = 'Blue Team' if team == StratRouletteTeam.BLUE else 'Orange Team'
        roleName = 'Attack' if role == StratRouletteTeamType.ATTACKER else 'Defense'

        await SendMessage(interaction, description='Changing Overtime role for {} to {}'.format(teamName, roleName), color=discord.Color.blue())

    def IsMatchInProgress(self):
        return self.activeMatch is not None