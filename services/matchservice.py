import discord
from discord.ext import commands
from utils.chatutils import SendMessage, SendChannelMessage
from datetime import datetime
from data.matchhistorydata import MatchResult, MatchHistoryData, MatchHistoryPlayerData
from enum import Enum
import random
import asyncio

class PlayerAlreadyQueued(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('Player {0.mention} is already queued.'.format(argument))

class PlayerNotQueued(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('Player {0.mention} is not currently queued.'.format(argument))

class PlayerNotQueuedOrInGame(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('Player {0.mention} is not currently queued or in a match.'.format(argument))

class InvalidMatchID(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('{} is not a valid match id.'.format(argument))

class PlayersNotSwapable(commands.BadArgument):
    def __init__(self, arg1, arg2):
        self.arg1 = arg1
        self.arg2 = arg2
        super().__init__('Player {0.mention} is not swapable with Player {1.mention}'.format(arg1, arg2))

class PlayerSwapFailed(commands.BadArgument):
    def __init__(self, arg1, arg2):
        self.arg1 = arg1
        self.arg2 = arg2
        super().__init__('Failed to find both Player {0.mention} and Player {1.mention} the queue/start matches.'.format(arg1, arg2))


class QueuedPlayer(object):
    user = None
    mmr = 0

    def __init__(self, user, mmr):
        self.user = user
        self.mmr = mmr

    def __eq__(self, other):
        if (other == None):
            return self.user == None
        return self.user.id == other.id

class FakeUser(object):
    id = 0
    mention = ''

    def __init__(self, id):
        self.id = id
        self.mention = '<Fake User: {}>'.format(id)

class Match(object):
    team1 = []
    team2 = []
    players = []
    map = ''
    pool = ''
    creationTime = ''
    uniqueID = 0
    matchMessage = None
    adminMessage = None
    resultsView = None

    def __init__(self, id, players, map, pool, creationTime):
        self.uniqueID = id
        self.map = map
        self.pool = pool
        self.creationTime = creationTime
        self.players = players.copy()

    def IsPlayerInMatch(self, user:discord.User):
        for player in self.players:
            if (player == user):
                return True
        return False

    def GetTeamAndNames(self, result:MatchResult):
        team1Name = 'Blue :blue_square:'
        team2Name = 'Orange :orange_square:'

        if result == MatchResult.TEAM1VICTORY or result == MatchResult.CANCELLED:
            return (self.team1, team1Name, self.team2, team2Name)
        elif result == MatchResult.TEAM2VICTORY:
            return (self.team2, team2Name, self.team1, team1Name)
        else:
            return None
    
    def StoreMatchHistoryData(self, winnerTeamData, loserTeamData, result:MatchResult):
        data = MatchHistoryData()

        if (result == MatchResult.TEAM1VICTORY or result == MatchResult.CANCELLED):
            data.StoreData(winnerTeamData, loserTeamData, result, self.map, self.pool, self.creationTime, self.uniqueID)
        elif (result == MatchResult.TEAM2VICTORY):
            data.StoreData(loserTeamData, winnerTeamData, result, self.map, self.pool, self.creationTime, self.uniqueID)

    def RemovePlayer(self, user:discord.User):
        for i in range(len(self.team1)):
            if (self.team1[i] == user):
                self.team1.pop(i)
                break

        for i in range(len(self.team2)):
            if (self.team2[i] == user):
                self.team2.pop(i)
                break

        for i in range(len(self.players)):
            if (self.players[i] == user):
                self.players.pop(i)
                break

    def AddPlayer(self, player):
        self.players.append(player)

    def BalanceTeams(self):
        team1 = []
        team2 = []

        numPlayers = len(self.players)
        team1Size = int(numPlayers / 2)
        team2Size = int(numPlayers - team1Size)
        minDiff = 2147483647

        def SumMMR(players):
            sum = 0
            for player in players:
                sum += player.mmr
            return sum

        for i in range(10):
            tempList = self.players.copy()
            random.shuffle(tempList) 

            tempT1 = tempList[:team1Size]
            tempT2 = tempList[team1Size:]

            team1Sum = SumMMR(tempT1)
            team2Sum = SumMMR(tempT2)

            diff = abs(team1Sum - team2Sum)
            if (diff < minDiff):
                team1 = tempT1
                team2 = tempT2
                minDiff = diff

        self.team1 = team1
        self.team2 = team2

class InvalidTeamResult(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('Team Result "{}" is not valid.'.format(argument))

class TeamResult(Enum):
    WIN = 0
    LOSE = 1
    CANCEL = 2
    INVALID = 3

    @classmethod
    async def convert(cls, argument):
        returnType = TeamResult.INVALID

        if (argument == TeamResult.WIN.value):
            returnType = TeamResult.WIN
        elif (argument == TeamResult.LOSE.value):
            returnType = TeamResult.LOSE
        elif (argument == TeamResult.CANCEL.value):
            returnType = TeamResult.CANCEL

        if (returnType is TeamResult.INVALID):
            raise InvalidTeamResult(argument)
        else:
            return returnType

class MatchResultView(discord.ui.View):
    def __init__(self, botSettings):
        # 3 hour timeout by default
        super().__init__(timeout=10800.0)
        self.result = MatchResult.INVALID
        self.user = None
        self.message = None
        self.botSettings = botSettings

    async def UpdateView(self, interaction:discord.Interaction, button:discord.ui.Button):
        for child in self.children:
            if child is not button:
                self.remove_item(child)
            else:
                child.disabled = True

        await interaction.response.edit_message(view=self)

    @discord.ui.button(label='Blue Win 🟦', style=discord.ButtonStyle.grey)
    async def CallForBlue(self, interaction:discord.Interaction, button:discord.ui.Button):
        await self.UpdateView(interaction, button)

        self.result = MatchResult.TEAM1VICTORY
        self.user = interaction.user
        self.stop()

    @discord.ui.button(label='Orange Win 🟧', style=discord.ButtonStyle.grey)
    async def CallForOrange(self, interaction:discord.Interaction, button:discord.ui.Button):
        await self.UpdateView(interaction, button)

        self.result = MatchResult.TEAM2VICTORY
        self.user = interaction.user
        self.stop()

    @discord.ui.button(label='Cancel ❎', style=discord.ButtonStyle.grey)
    async def CancelMatch(self, interaction:discord.Interaction, button:discord.ui.Button):
        await self.UpdateView(interaction, button)

        self.result = MatchResult.CANCELLED
        self.user = interaction.user
        self.stop()

    async def interaction_check(self, interaction:discord.Interaction):
        return self.botSettings.IsUserAdmin(interaction.user)

    async def on_timeout(self):
        for child in self.children:
            if child.label != 'Cancel ❎':
                self.remove_item(child)
            else:
                child.disabled = True
        
        if self.message is not None:
            await self.message.edit(view=self)

        self.result = MatchResult.CANCELLED
        self.user = None

class MatchService(object):
    queuedPlayers = []
    matchesStarted = {}
    bot = None
    botSettings = None
    forcedMap = None

    def Init(self, bot, botSettings):
        self.bot = bot
        self.botSettings = botSettings

    def GetNotInQueue(self, members):
        missing = []

        for memberID in members.keys():
            found = False
            for player in self.queuedPlayers:
                if player.user.id == memberID:
                    found = True

            if (not found):
                missing.append(memberID)

        return missing

    async def JoinQueue(self, interaction:discord.Interaction, user:discord.Member):
        mmr = self.botSettings.GetMMR(user)

        self.queuedPlayers.append(QueuedPlayer(user, mmr))

        numPlayers = len(self.queuedPlayers)

        if (numPlayers == 10):
            description = '{0.mention} [{1}] joined the queue.\nThe queue is now full, starting a match...'.format(user, mmr)
        else:
            description = '**[{0}/10]** {1.mention} [{2}] joined the queue.'.format(numPlayers, user, mmr)
        
        await SendMessage(interaction, description=description, color=discord.Color.blue())

        if (numPlayers == 10):
            await self.StartMatch(False)

    async def LeaveQueue(self, interaction:discord.Interaction, user:discord.Member):
        mmr = 0
        for i in range(len(self.queuedPlayers)):
            if (self.queuedPlayers[i] == user):
                mmr = self.queuedPlayers[i].mmr
                self.queuedPlayers.pop(i)
                break

        numPlayers = len(self.queuedPlayers)

        if (numPlayers == 0):
            description = '{0.mention} [{1}] left the queue.\nThe queue is now empty.'.format(user, mmr)
            self.forcedMap = None
        else:
            description = '**[{0}/10]** {1.mention} [{2}] left the queue.'.format(numPlayers, user, mmr)

        await SendMessage(interaction, description=description, color=discord.Color.blue())

    async def ShowQueue(self, interaction:discord.Interaction):
        numPlayers = len(self.queuedPlayers)

        if (numPlayers == 0):
            description = 'The queue is empty.'
            await SendMessage(interaction, description=description, color=discord.Color.blue())
        else:
            title = 'Lobby [{0}/10]'.format(numPlayers)
            description = ''
            isFirst = True

            for player in self.queuedPlayers:
                if (isFirst):
                    isFirst = False
                else:
                    description += '\n'

                description += '[{1}] {0.mention}'.format(player.user, player.mmr)

            await SendMessage(interaction, title=title, description=description, color=discord.Color.blue())

    async def ClearQueue(self, interaction:discord.Interaction):
        self.queuedPlayers.clear()
        self.forcedMap = None

        await SendMessage(interaction, description='Queue Cleared.', color=discord.Color.blue())

    async def KickFromQueue(self, interaction:discord.Interaction, user:discord.Member):
        mmr = 0
        found = False
        for i in range(len(self.queuedPlayers)):
            if (self.queuedPlayers[i] == user):
                mmr = self.queuedPlayers[i].mmr
                self.queuedPlayers.pop(i)
                found = True
                break

        numPlayers = len(self.queuedPlayers)

        if (found == False):
            description = '{0.mention} is not in the queue.'.format(user)
        elif (numPlayers == 0):
            description = '{0.mention} [{1}] was removed from the queue by {2.mention}.\nThe queue is now empty.'.format(user, mmr, interaction.user)
            self.forcedMap = None
        else:
            description = '**[{0}/10]** {1.mention} [{2}] was removed from the queue by {3.mention}.'.format(numPlayers, user, mmr, interaction.user)

        await SendMessage(interaction, description=description, color=discord.Color.blue())

    async def SwapPlayers(self, interaction:discord.Interaction, user1, user2):
        # TODO: test this, make sure deleting the old match message doesn't cause issue
        # Re-test the match starting functionality. I rewrote some of it 

        # Figure out who is in queue and who is in a match first
        queuedPlayer = None
        matchPlayer = None
        matchID = -1

        # Find the queued player
        for player in self.queuedPlayers:
            if (player == user1 or player == user2):
                queuedPlayer = player
                break

        # Find the match player
        for match in self.matchesStarted.values():
            if (match.IsPlayerInMatch(user1)):
                matchPlayer = user1
                matchID = match.uniqueID
                break
            elif (match.IsPlayerInMatch(user2)):
                matchPlayer = user2
                matchID = match.uniqueID
                break

        if (queuedPlayer == None or matchPlayer == None or matchID == -1):
            raise PlayerSwapFailed(user1, user2)

        # Delete the old message
        try:
            await self.matchesStarted[matchID].matchMessage.delete()
        except:
            pass

        messageID = self.matchesStarted[matchID].adminMessage.id
        try:
            await self.matchesStarted[matchID].adminMessage.delete()
        except:
            pass

        self.matchesStarted[matchID].matchMessage = None
        self.matchesStarted[matchID].adminMessage = None

        # Remove the queued player
        mmr = 0
        for i in range(len(self.queuedPlayers)):
            if (self.queuedPlayers[i] == queuedPlayer.user):
                mmr = self.queuedPlayers[i].mmr
                self.queuedPlayers.pop(i)
                break

        # Remove the match player
        self.matchesStarted[matchID].RemovePlayer(matchPlayer)

        # Add match player to queue
        tempMMR = self.botSettings.GetMMR(matchPlayer)
        self.queuedPlayers.append(QueuedPlayer(matchPlayer, tempMMR))

        # Add queued player to match
        self.matchesStarted[matchID].AddPlayer(queuedPlayer)

        self.matchesStarted[matchID].BalanceTeams()

        self.matchesStarted[matchID].resultsView.stop()
        self.matchesStarted[matchID].resultsView = MatchResultView(self.botSettings)

        await SendMessage(interaction, description='{0.mention} has been swapped with {1.mention}!'.format(queuedPlayer.user, matchPlayer), color=discord.Color.blue())
        message, adminMessage = await self.SendMatchMessages(self.matchesStarted[matchID])

        self.matchesStarted[matchID].matchMessage = message
        self.matchesStarted[matchID].adminMessage = adminMessage

        await self.WaitForMatchResult(matchID)

    def UpdateMMR(self, user:discord.Member, mmr:int):
        for player in self.queuedPlayers:
            if (player == user):
                player.mmr = mmr
                break;

    async def ForceMap(self, interaction:discord.Interaction, map):
        if (len(self.matchesStarted) > 0):
            key = list(self.matchesStarted.keys())[0]
            self.matchesStarted[key].map = map

            await SendMessage(interaction, description='The map for Game #{} has been changed to {}.'.format(key, map), color=discord.Color.blue())

            # Delete the old message
            try:
                await self.matchesStarted[key].matchMessage.delete()
            except:
                pass

            messageID = self.matchesStarted[key].adminMessage.id
            try:
                await self.matchesStarted[key].adminMessage.delete()
            except:
                pass

            self.matchesStarted[key].matchMessage = None
            self.matchesStarted[key].adminMessage = None

            self.matchesStarted[key].resultsView.stop()
            self.matchesStarted[key].resultsView = MatchResultView(self.botSettings)

            # Send an updated message
            message, adminMessage = await self.SendMatchMessages(self.matchesStarted[key])

            self.matchesStarted[key].matchMessage = message
            self.matchesStarted[key].adminMessage = adminMessage

            await self.WaitForMatchResult(key)

        elif (len(self.queuedPlayers) > 0):
            self.forcedMap = map
            await SendMessage(interaction, description='The next map will be {}.'.format(map), color=discord.Color.blue())
        else:
            await SendMessage(interaction, description='You can only force a map when there is a match running or players in the queue.', color=discord.Color.red())

    def IsMatchInProgress(self):
        return len(self.matchesStarted) > 0

    async def ForceMapPool(self, interaction:discord.Interaction, pool:str):
        key = list(self.matchesStarted.keys())[0]
        self.matchesStarted[key].pool = pool 

        selectedMap = self.matchesStarted[key].map

        # If the current map isn't in the map pool, reroll the map
        if (not self.botSettings.IsValidMapPoolMap(pool, selectedMap)):
            await SendMessage(interaction, description='The map pool for Game #{} has been changed to {}. The map {} is not in the pool, re-rolling map!'.format(key, pool, selectedMap), color=discord.Color.blue())
            await self.RerollMap(interaction, useInteraction=False)
            return

        await SendMessage(interaction, description='The map pool for Game #{} has been changed to {}.'.format(key, pool), color=discord.Color.blue())

        # Delete the old message
        try:
            await self.matchesStarted[key].matchMessage.delete()
        except:
            pass

        messageID = self.matchesStarted[key].adminMessage.id
        try:
            await self.matchesStarted[key].adminMessage.delete()
        except:
            pass

        self.matchesStarted[key].matchMessage = None
        self.matchesStarted[key].adminMessage = None

        self.matchesStarted[key].resultsView.stop()
        self.matchesStarted[key].resultsView = MatchResultView(self.botSettings)

        # Send an updated message
        message, adminMessage = await self.SendMatchMessages(self.matchesStarted[key])

        self.matchesStarted[key].matchMessage = message
        self.matchesStarted[key].adminMessage = adminMessage

        await self.WaitForMatchResult(key)

    async def RerollMap(self, interaction:discord.Interaction, useInteraction:bool):
        key = list(self.matchesStarted.keys())[0]

        enablePMCCOverride = False

        for player in self.matchesStarted[key].players:
            if (player.user.id == int('90342358620573696')):
                enablePMCCOverride = True
                break

        selectedMap = self.botSettings.GetRandomMap(self.matchesStarted[key].pool, enablePMCCOverride).name

        self.matchesStarted[key].map = selectedMap 

        description = 'The map for Game #{} has been changed to {}.'.format(key, selectedMap)

        if useInteraction:
            await SendMessage(interaction, description=description, color=discord.Color.blue())
        else:
            await SendChannelMessage(interaction.channel, description=description, color=discord.Color.blue())

        # Delete the old message
        try:
            await self.matchesStarted[key].matchMessage.delete()
        except:
            pass

        messageID = self.matchesStarted[key].adminMessage.id
        try:
            await self.matchesStarted[key].adminMessage.delete()
        except:
            pass

        self.matchesStarted[key].matchMessage = None
        self.matchesStarted[key].adminMessage = None

        self.matchesStarted[key].resultsView.stop()
        self.matchesStarted[key].resultsView = MatchResultView(self.botSettings)

        # Send an updated message
        message, adminMessage = await self.SendMatchMessages(self.matchesStarted[key])

        self.matchesStarted[key].matchMessage = message
        self.matchesStarted[key].adminMessage = adminMessage

        await self.WaitForMatchResult(key)

    async def SendMatchMessages(self, match):
        title = 'Game #{} Started'.format(match.uniqueID)
        description = '**Creation Time:** {}\n**Map:** {}\n**Map Pool:** {}'.format(match.creationTime, match.map, 'None' if match.pool is None else match.pool)
        thumbnail = self.botSettings.GetMapThumbnail(match.map)

        team1Field = {}
        team1Field['name'] = 'Team Blue :blue_square:'
        team1Field['value'] = ''
        team1Field['inline'] = False
        
        team2Field = {}
        team2Field['name'] = 'Team Orange :orange_square:'
        team2Field['value'] = ''
        team2Field['inline'] = False		
    
        if (len(match.team1) > 0):
            isFirst = True
            mmrSum = 0
            for player in match.team1:
                if (isFirst):
                    isFirst = False
                else:
                    team1Field['value'] += '\n'
                mmrSum += player.mmr

                team1Field['value'] += '{0.mention}'.format(player.user)

            team1Field['name'] = '[{}] {}'.format(mmrSum, team1Field['name'])
        else:
            team1Field['value'] = 'Empty'

        if (len(match.team2) > 0):
            isFirst = True
            mmrSum = 0
            for player in match.team2:
                if (isFirst):
                    isFirst = False
                else:
                    team2Field['value'] += '\n'
                mmrSum += player.mmr

                team2Field['value'] += '{0.mention}'.format(player.user)

            team2Field['name'] = '[{}] {}'.format(mmrSum, team2Field['name'])
        else:
            team2Field['value'] = 'Empty'

        await self.bot.change_presence(activity=discord.Game(name='on {}'.format(match.map)))

        adminField = {}
        adminField['name'] = 'Report the result!'
        adminField['value'] = 'Team Blue Win :blue_square:\nTeam Orange Win :orange_square:\nCancelled :negative_squared_cross_mark:'
        adminField['inline'] = False	

        message = await SendChannelMessage(self.botSettings.lobbyChannel, title=title, description=description, thumbnail=thumbnail, fields=[team1Field, team2Field], color=discord.Color.blue())
        adminMessage = await SendChannelMessage(self.botSettings.reportChannel, title=title, description=description, thumbnail=thumbnail, fields=[team1Field, team2Field, adminField], view=match.resultsView)

        match.resultsView.message = adminMessage

        return message, adminMessage

    async def StartMatch(self, fillWithFakePlayers:bool):
        if (fillWithFakePlayers and len(self.queuedPlayers) < 10):
            # Use negative ids so that we know its fake
            fakeID = -1
            while (len(self.queuedPlayers) < 10):
                self.queuedPlayers.append(QueuedPlayer(FakeUser(fakeID), 100))
                fakeID -= 1

        # Check for PMCC override
        enablePMCCOverride = False

        for player in self.queuedPlayers:
            if (player.user.id == int('90342358620573696')):
                enablePMCCOverride = True
                break

        id = self.botSettings.GetNextUniqueMatchID()
        selectedPool = self.botSettings.currentPool
        selectedMap = self.botSettings.GetRandomMap(selectedPool, enablePMCCOverride).name
        creationTime = datetime.strftime(datetime.now(), '%d %b %Y %H:%M')

        if (self.forcedMap is not None):
            selectedMap = self.forcedMap
            self.forcedMap = None

        newMatch = Match(id, self.queuedPlayers, selectedMap, selectedPool, creationTime)
        self.matchesStarted[id] = newMatch
        self.queuedPlayers.clear()

        newMatch.BalanceTeams()

        newMatch.resultsView = MatchResultView(self.botSettings)
    
        message, adminMessage = await self.SendMatchMessages(newMatch)
        
        newMatch.matchMessage = message
        newMatch.adminMessage = adminMessage 

        await self.WaitForMatchResult(id)

    async def WaitForMatchResult(self, id):
        view = self.matchesStarted[id].resultsView
        # Wait for an admin to report the results
        try:
            timedOut = await view.wait()
        except:
            print('Something has gone very wrong here')
            return

        if (timedOut):
            await self.CallMatch(self.bot.user, id, MatchResult.CANCELLED)
            return

        # If the view is invalid for whatever reason, just don't call the match
        if (view.result == MatchResult.INVALID):
            print('There is no result so ignore this view')
            return

        if (view.user == None):
            view.user = self.bot.user

        await self.CallMatch(view.user, id, view.result)

    # Union[discord.Member, FakeUser] member 
    async def UpdateRoles(self, member, oldRole, newRole):
        if (isinstance(member, FakeUser)):
            return

        if (oldRole is not None):
            try:
                await member.remove_roles(oldRole.role, reason='Match service is updating MMR Role for {}'.format(member))
            except discord.HTTPException:
                await SendChannelMessage(self.botSettings.resultsChannel, description='Failed to remove previous rank. Please try again.', color=discord.Color.red())

        if (newRole is not None):
            try:
                await member.add_roles(newRole.role, reason='Match service is updating MMR Role for {}'.format(member))
            except discord.HTTPException:
                await SendChannelMessage(self.botSettings.resultsChannel, description='Failed to add new rank. Please try again.', color=discord.Color.red())

    async def GetTeamData(self, team, teamName, result:TeamResult):
        teamData = []
        teamField = {}
        teamField['name'] = '{}: Team {}'.format('Winner' if result == TeamResult.WIN else 'Loser', teamName)
        teamField['value'] = ''
        teamField['inline'] = False

        if (len(team) > 0):
            isFirst = True

            for player in team:
                oldMMR = 0
                newMMR = 0
                oldRole = None
                newRole = None
                mmrDelta = 0

                if (result == TeamResult.WIN):
                    oldMMR, newMMR, oldRole, newRole, mmrDelta = self.botSettings.DeclareWinner(player.user)
                elif (result == TeamResult.LOSE):
                    oldMMR, newMMR, oldRole, newRole, mmrDelta = self.botSettings.DeclareLoser(player.user)
                else:
                    oldMMR, newMMR, mmrDelta = self.botSettings.DeclareCancel(player.user)

                delta = int(abs(newMMR - oldMMR))
                teamData.append(MatchHistoryPlayerData(_id=player.user.id, _prevMMR=oldMMR, _newMMR=newMMR, _mmrDelta=mmrDelta))

                if (isFirst):
                    isFirst = False
                else:
                    teamField['value'] += '\n'

                sign = '+' if result == TeamResult.WIN else '-'

                teamField['value'] += '**{}** {} {} {} = {}'.format(self.botSettings.GetUserName(player.user), oldMMR, sign, delta, newMMR)

                if (oldRole is not None and newRole is not None):
                    teamField['value'] += ' **Rank:** {0.mention} -> {1.mention}'.format(oldRole.role, newRole.role)

                # No point in updating roles if the match was cancelled
                if (result != TeamResult.CANCEL):
                    await self.UpdateRoles(player.user, oldRole, newRole)
        else:
            teamField['value'] = 'Empty'

        return teamData, teamField

    async def CallMatch(self, user:discord.Member, id:int, matchResult:MatchResult):
        print('Match {} has been called as {}'.format(id, matchResult))

        if (id not in self.matchesStarted):
            raise InvalidMatchID(id)

        title = 'Match Results: Game #{}'.format(id)
        footer = 'This match was called by {}'.format(user)
        description = '**Creation Time:** {}\n**Map:** {}\n**Map Pool:** {}'.format(self.matchesStarted[id].creationTime, self.matchesStarted[id].map, 'None' if self.matchesStarted[id].pool is None else self.matchesStarted[id].pool)
        thumbnail = self.botSettings.GetMapThumbnail(self.matchesStarted[id].map)

        winnerTeam, winnerName, loserTeam, loserName = self.matchesStarted[id].GetTeamAndNames(matchResult)

        await self.bot.change_presence(activity=None)

        if (matchResult == MatchResult.CANCELLED):
            description += '\n\nThis match has been cancelled.'

            team1Data, team1Field = await self.GetTeamData(winnerTeam, winnerName, TeamResult.CANCEL)
            team2Data, team2Field = await self.GetTeamData(loserTeam, loserName, TeamResult.CANCEL)

            self.matchesStarted[id].StoreMatchHistoryData(team1Data, team2Data, matchResult)
            del self.matchesStarted[id]

            await SendChannelMessage(self.botSettings.resultsChannel, title=title, description=description, thumbnail=thumbnail, footer=footer, color=discord.Color.blue())
            return

        winnerTeamData, winnerField = await self.GetTeamData(winnerTeam, winnerName, TeamResult.WIN)
        loserTeamData, loserField = await self.GetTeamData(loserTeam, loserName, TeamResult.LOSE)

        self.botSettings.DeclareMapPlayed(self.matchesStarted[id].map, self.matchesStarted[id].pool)

        self.matchesStarted[id].StoreMatchHistoryData(winnerTeamData, loserTeamData, matchResult)
        del self.matchesStarted[id]

        await SendChannelMessage(self.botSettings.resultsChannel, title=title, description=description, thumbnail=thumbnail, fields=[winnerField, loserField], footer=footer, color=discord.Color.blue())

    def IsPlayerQueued(self, user:discord.User):
        for player in self.queuedPlayers:
            if player == user:
                return True

        return False

    def IsPlayerInGame(self, user:discord.User):
        for match in self.matchesStarted.values():
            if match.IsPlayerInMatch(user):
                return True
        return False

    # Only supports the first match found. Won't work for other matches
    def GetTeam1Players(self):
        if len(self.matchesStarted) == 0:
            return []

        key = list(self.matchesStarted.keys())[0]
        match = self.matchesStarted[key]
        return [ player.user for player in match.team1 ]

    def GetTeam2Players(self):
        if len(self.matchesStarted) == 0:
            return []

        key = list(self.matchesStarted.keys())[0]
        match = self.matchesStarted[key]
        return [ player.user for player in match.team2 ]
