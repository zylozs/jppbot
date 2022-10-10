import discord
from discord.ext import commands
from data.stratroulettedata import StratRouletteTeam, StratRouletteTeamType
from utils.chatutils import EditMessage, EditViewMessage, SendChannelMessage, SendMessage, SendMessageEdit

class StratRouletteMatchIsActive(commands.BadArgument):
    def __init__(self):
        super().__init__('There is already an active strat roulette match. Please finish it first before starting a new one.')

class StratRouletteMatchAlreadyQueued(commands.BadArgument):
    def __init__(self):
        super().__init__('There is already a strat roulette match queued.')

class CantStartStratRoulette(commands.BadArgument):
    def __init__(self):
        super().__init__("Can't start Strat Roulette when a match isn't running")

class CantStopStratRoulette(commands.BadArgument):
    def __init__(self):
        super().__init__("Can't stop Strat Roulette when one isn't running")

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

class StratRouletteOvertimeRoleDropdownView(discord.ui.View):
    result = StratRouletteTeamType.INVALID
    def __init__(self, team, service, allowRepeatRole):
        # 1 min timeout
        super().__init__(timeout=60.0)

        self.team = team
        self.service = service
        self.allowRepeatRole = allowRepeatRole

    @discord.ui.select(placeholder='Choose which overtime role your team is...', options=[
        discord.SelectOption(label='Attack'),
        discord.SelectOption(label='Defense'),
        discord.SelectOption(label='Cancel')
    ])
    async def SelectRole(self, interaction:discord.Interaction, select:discord.ui.Select):
        if (select.values[0] == 'Cancel'):
            await EditViewMessage(interaction, description='Cancelling the overtime role change.', color=discord.Color.blue())
            self.stop()
            return

        # Validate the role is different if we don't allow repeat roles
        if (not self.allowRepeatRole):
            if (select.values[0] == 'Attack' and self.team.type == StratRouletteTeamType.ATTACKER):
                await EditViewMessage(interaction, view=self, description='Team {} is already Attacking.'.format(self.team.name), color=discord.Color.red())
                return
            elif (select.values[0] == 'Defense' and self.team.type == StratRouletteTeamType.DEFENDER):
                await EditViewMessage(interaction, view=self, description='Team {} is already Defending.'.format(self.team.name), color=discord.Color.red())
                return

        await EditViewMessage(interaction, description="Setting Team {}'s overtime role to {}".format(self.team.name, select.values[0]), color=discord.Color.blue())
        self.stop()

        if (select.values[0] == 'Attack'):
            self.result = StratRouletteTeamType.ATTACKER
        else:
            self.result = StratRouletteTeamType.DEFENDER

class StratRouletteStratViewBase(discord.ui.View):
    def __init__(self, service, teamData:StratRouletteTeamData, roundNumber:int):
        # 1 hour timeout by default
        super().__init__(timeout=3600.0)
        self.service = service
        self.botSettings = service.botSettings
        self.team = teamData
        self.roundNumber = roundNumber

    async def ValidateTeam(self, interaction:discord.Interaction, message:str):
        if (interaction.user not in self.team.members):
            await SendMessage(interaction, description=message, color=discord.Color.red(), ephemeral=True)
            return False

        return True

    async def ValidateRound(self, interaction:discord.Interaction, extraMessage:str):
        if (self.service.activeMatch is None or self.roundNumber != self.service.activeMatch.roundNumber):
            await SendMessage(interaction, description='The round has already changed.{}'.format(extraMessage), color=discord.Color.red(), ephemeral=True)
            return False

        return True

    async def ReValidateRound(self, interaction:discord.Interaction, extraMessage:str):
        if (self.service.activeMatch is None or self.roundNumber != self.service.activeMatch.roundNumber):
            await SendMessageEdit(interaction, description='The round has already changed.{}'.format(extraMessage), color=discord.Color.red(), ephemeral=True)
            return False

        return True

    async def ValidateAdmin(self, interaction:discord.Interaction):
        if (not self.botSettings.IsUserAdmin(interaction.user)):
            await SendMessage(interaction, description='You must be an admin to perform this action!', color=discord.Color.red(), ephemeral=True)
            return False

        return True

    async def OvertimeButtonBase(self, interaction:discord.Interaction):
        if (not await self.ValidateAdmin(interaction)):
            return
        
        if (not await self.ValidateRound(interaction, ' Try using the latest strat\'s button!')):
            self.stop()
            return

        roleDropdown = StratRouletteOvertimeRoleDropdownView(self.team, self.service, allowRepeatRole=False)
        await interaction.response.send_message(view=roleDropdown, ephemeral=True)

        timeout = await roleDropdown.wait()
        if (timeout):
            await SendMessageEdit(interaction, description='The Overtime Role selection has timed out. Try again.', color=discord.Color.blue())

        # Revalidate the round to make sure it didn't change while we waited on user input
        if (not await self.ReValidateRound(interaction, ' Looks like someone beat you to it!')):
            self.stop()
            return

        if (roleDropdown.result != StratRouletteTeamType.INVALID):
            self.service.SetOvertimeRole(self.team, roleDropdown.result)
            await self.service.UpdateOvertimeStrats()

    @discord.ui.button(label='Reroll (1)', style=discord.ButtonStyle.green)
    async def RerollStrat(self, interaction:discord.Interaction, button:discord.ui.Button):
        if (not await self.ValidateTeam(interaction, 'Only members in Team {} can reroll their strat!'.format(self.team.name))):
            return
        
        if (not await self.ValidateRound(interaction, ' You can no longer reroll the previous strat.')):
            self.stop()
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

    async def DisableButtons(self):
        for child in self.children:
            child.disabled = True

        self.stop()

class StratRouletteNormalRoundView(StratRouletteStratViewBase):
    @discord.ui.button(label='Next Round ⏩️', style=discord.ButtonStyle.blurple)
    async def BeginNextRound(self, interaction:discord.Interaction, button:discord.ui.Button):
        if (not await self.ValidateTeam(interaction, 'You aren\'t a part of Team {}! What are you doing spying?'.format(self.team.name))):
            return
        
        if (not await self.ValidateRound(interaction, ' Looks like someone beat you to it!')):
            self.stop()
            return

        button.disabled = True

        await interaction.response.edit_message(view=self)
        await self.service.StartNextRound()

        self.stop()

class StratRouletteLastRoundView(StratRouletteStratViewBase):
    @discord.ui.button(label='Start Overtime', style=discord.ButtonStyle.blurple)
    async def BeginNextRound(self, interaction:discord.Interaction, button:discord.ui.Button):
        if (not await self.ValidateTeam(interaction, 'You aren\'t a part of Team {}! What are you doing spying?'.format(self.team.name))):
            return
        
        if (not await self.ValidateRound(interaction, ' Looks like someone beat you to it!')):
            self.stop()
            return

        roleDropdown = StratRouletteOvertimeRoleDropdownView(self.team, self.service, allowRepeatRole=True)
        await interaction.response.send_message(view=roleDropdown, ephemeral=True)

        timeout = await roleDropdown.wait()
        if (timeout):
            await SendMessageEdit(interaction, description='The Overtime Role selection has timed out. Try again.', color=discord.Color.blue())
            return

        # Revalidate the round to make sure it didn't change while we waited on user input
        if (not await self.ReValidateRound(interaction, ' Looks like someone beat you to it!')):
            self.stop()
            return

        if (roleDropdown.result != StratRouletteTeamType.INVALID):
            self.service.SetOvertimeRole(self.team, roleDropdown.result)
            await self.service.StartNextRound()
            self.stop()

class StratRouletteOvertimeRoundView(StratRouletteNormalRoundView):
    @discord.ui.button(label='Fix Overtime 🛠️', style=discord.ButtonStyle.grey)
    async def FixOvertimeRole(self, interaction:discord.Interaction, button:discord.ui.Button):
        await self.OvertimeButtonBase(interaction)

class StratRouletteLastOvertimeRoundView(StratRouletteStratViewBase):
    @discord.ui.button(label='Fix Overtime 🛠️', style=discord.ButtonStyle.grey)
    async def FixOvertimeRole(self, interaction:discord.Interaction, button:discord.ui.Button):
        await self.OvertimeButtonBase(interaction)

class StratRouletteMatch(object):
    team1 = None
    team2 = None
    overtimeRoleTeam1 = StratRouletteTeamType.INVALID

    roundNumber = 0

    def __init__(self, team1:list[discord.Member], team1Type:StratRouletteTeamType, team2:list[discord.Member], team2Type:StratRouletteTeamType):
        self.team1 = StratRouletteTeamData(team1, team1Type, 'Blue :blue_square:')
        self.team2 = StratRouletteTeamData(team2, team2Type, 'Orange :orange_square:')

    def RollSwap(self):
        tempType = self.team1.type
        self.team1.type = self.team2.type
        self.team2.type = tempType

    def BeginOvertime(self):
        invertedRole = StratRouletteTeamType.ATTACKER if self.overtimeRoleTeam1 == StratRouletteTeamType.DEFENDER else StratRouletteTeamType.DEFENDER

        self.team1.type = self.overtimeRoleTeam1
        self.team2.type = invertedRole

    def FixOvertimeRoles(self):
        self.BeginOvertime()

def GetFieldFromTeam(roundNumber:int, team:StratRouletteTeamData):
    typeName = 'Attack' if team.type == StratRouletteTeamType.ATTACKER else 'Defense'
    extraRoundInfo = ':rotating_light: OVERTIME :rotating_light: ' if roundNumber >= 7 else ''
    field = {}
    field['name'] = '{2}Round {0} Strat - {1}'.format(roundNumber, typeName, extraRoundInfo)
    field['value'] = '**{}**\n\n{}'.format(team.strat.title, team.strat.strat)
    field['inline'] = False
    return field

def GetTitleFromTeam(team:StratRouletteTeamData):
    description = '**Team {}**\n'.format(team.name)

    for member in team.members:
        if member is not None:
            description += '{0.mention}'.format(member)

    return description

def GetViewFromRound(service, team, roundNumber:int):
    if (roundNumber < 6):
        return StratRouletteNormalRoundView(service, team, roundNumber)
    elif (roundNumber == 6):
        return StratRouletteLastRoundView(service, team, roundNumber)
    elif (roundNumber >= 7 and roundNumber < 9):
        return StratRouletteOvertimeRoundView(service, team, roundNumber)
    elif (roundNumber >= 9):
        return StratRouletteLastOvertimeRoundView(service, team, roundNumber)
    return None

class StratRouletteService(object):
    bot = None
    botSettings = None
    activeMatch = None
    startQueued = False
    forcedPool = ''

    def Init(self, bot, botSettings):
        self.bot = bot
        self.botSettings = botSettings

    def ClearQueuedMatch(self):
        self.startQueued = False
        self.forcedPool = ''

    async def QueueStartMatch(self, forcedPool:str = ''):
        if (self.activeMatch is not None):
            raise StratRouletteMatchIsActive()

        if (self.startQueued):
            raise StratRouletteMatchAlreadyQueued()

        self.startQueued = True
        self.forcedPool = forcedPool

    def IsMatchQueued(self):
        return self.startQueued

    async def TryStartQueuedMatch(self, attackers:list[discord.Member], defenders:list[discord.Member] ):
        if (self.startQueued):
            self.startQueued = False
            await self.StartMatch(attackers, defenders)
            return True

        return False

    async def StopMatch(self):
        if (self.activeMatch is None):
            raise CantStopStratRoulette()

        if self.activeMatch.team1.stratView:
            await self.activeMatch.team1.stratView.DisableButtons()
            await self.activeMatch.team1.stratMessage.edit(view=self.activeMatch.team1.stratView)

        if self.activeMatch.team2.stratView:
            await self.activeMatch.team2.stratView.DisableButtons()
            await self.activeMatch.team2.stratMessage.edit(view=self.activeMatch.team2.stratView)

        await SendChannelMessage(self.botSettings.lobbyChannel, description='_puts down the revolver_ Thanks for playing Strat Roulette!', color=discord.Color.blue())

        self.activeMatch = None
        self.forcedPool = ''

    async def StartMatch(self, attackers:list[discord.Member], defenders:list[discord.Member]):
        if (self.activeMatch is not None):
            raise StratRouletteMatchIsActive()

        self.activeMatch = StratRouletteMatch(attackers, StratRouletteTeamType.ATTACKER, defenders, StratRouletteTeamType.DEFENDER)

        self.activeMatch.team1.channel = self.botSettings.blueTeamChannel
        self.activeMatch.team2.channel = self.botSettings.orangeTeamChannel

        self.activeMatch.team1.type = StratRouletteTeamType.ATTACKER
        self.activeMatch.team2.type = StratRouletteTeamType.DEFENDER

        await self.StartNextRound()

    async def SendStrat(self, team:StratRouletteTeamData, sendNewMessage = True):
        description = GetTitleFromTeam(team)

        if (sendNewMessage):
            team.stratView = GetViewFromRound(self, team, self.activeMatch.roundNumber)

        field = GetFieldFromTeam(self.activeMatch.roundNumber, team)
        
        if (sendNewMessage):
            team.stratMessage = await SendChannelMessage(team.channel, description=description, fields=[field], color=discord.Color.blue(), view=team.stratView)
        else:
            try:
                await EditMessage(team.stratMessage, description=description, fields=[field], color=discord.Color.blue(), view=team.stratView)
            except:
                pass

    async def StartNextRound(self):
        if self.activeMatch.team1.stratView:
            await self.activeMatch.team1.stratView.DisableButtons()
            await self.activeMatch.team1.stratMessage.edit(view=self.activeMatch.team1.stratView)

        if self.activeMatch.team2.stratView:
            await self.activeMatch.team2.stratView.DisableButtons()
            await self.activeMatch.team2.stratMessage.edit(view=self.activeMatch.team2.stratView)

        self.activeMatch.roundNumber += 1

        # Role swap!
        if (self.activeMatch.roundNumber == 4):
            self.activeMatch.RollSwap()
        # Overtime!
        elif (self.activeMatch.roundNumber == 7):
            self.activeMatch.BeginOvertime()
        elif (self.activeMatch.roundNumber > 7 and self.activeMatch.roundNumber < 10):
            self.activeMatch.RollSwap()
        # Match is over, dont do anything more
        elif (self.activeMatch.roundNumber >= 10):
            return

        self.activeMatch.team1.strat = self.botSettings.GetRandomStrat(self.activeMatch.team1.type, self.activeMatch.team1.strat)
        self.activeMatch.team2.strat = self.botSettings.GetRandomStrat(self.activeMatch.team2.type, self.activeMatch.team2.strat)

        self.activeMatch.team1.canReroll = True
        self.activeMatch.team2.canReroll = True

        await self.SendStrat(self.activeMatch.team1)
        await self.SendStrat(self.activeMatch.team2)

    async def UpdateTeams(self, team1:list[discord.Member], team2:list[discord.Member]):
        self.activeMatch.team1.members = team1
        self.activeMatch.team2.members = team2

        await self.SendStrat(self.activeMatch.team1, sendNewMessage = False)
        await self.SendStrat(self.activeMatch.team2, sendNewMessage = False)

    def SetOvertimeRole(self, team:StratRouletteTeam, role:StratRouletteTeamType):
        if (self.activeMatch.team1 == team):
            self.activeMatch.overtimeRoleTeam1 = role
        else:
            invertedRole = StratRouletteTeamType.ATTACKER if role == StratRouletteTeamType.DEFENDER else StratRouletteTeamType.DEFENDER
            self.activeMatch.overtimeRoleTeam1 = invertedRole

        # If overtime has already started, update the teams directly
        if (self.activeMatch.roundNumber >= 7):
            self.activeMatch.FixOvertimeRoles()

    async def UpdateOvertimeStrats(self):
        # Reroll the invalid strats for the updated roles
        if (self.activeMatch.team1.strat.type != StratRouletteTeamType.BOTH):
            self.activeMatch.team1.strat = self.botSettings.GetRandomStrat(self.activeMatch.team1.type)

        if (self.activeMatch.team2.strat.type != StratRouletteTeamType.BOTH):
            self.activeMatch.team2.strat = self.botSettings.GetRandomStrat(self.activeMatch.team2.type)

        await self.SendStrat(self.activeMatch.team1, sendNewMessage = False)
        await self.SendStrat(self.activeMatch.team2, sendNewMessage = False)

    def IsMatchInProgress(self):
        return self.activeMatch is not None