from __future__ import barry_as_FLUFL
from data.botsettings import ChannelType, RegisteredRoleUnitialized, InvalidGuild
from data.playerdata import UserNotRegistered, UserAlreadyRegistered
from data.matchhistorydata import MatchHistoryData, MatchResult
from data.quipdata import QuipType
from data.mappool import MapPoolType
from data.stratroulettedata import StratRouletteTeamType, NoStratRouletteStrats, InvalidStratRouletteTeamType
from services.matchservice import PlayerAlreadyQueued, PlayerNotQueued
from utils.chatutils import SendMessage, SendMessages
from utils.botutils import IsValidChannel, IsActivePlayer, GuildCommand
from utils.errorutils import HandleError, HandleAppError
from globals import *
from discord.ext import commands, tasks
from datetime import datetime
from discord import app_commands
from discord.app_commands import Choice
import discord
import random

class BotCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        self.OnUpdateStatus.cancel()
        return super().cog_unload()

    @tasks.loop(minutes=30)
    async def OnUpdateStatus(self):
        print('Changing status!')

        # Dont override matchmaking
        if (len(matchService.matchesStarted) > 0):
            return

        # Golfit session time
        now = datetime.now()
        day = now.weekday() # 1 == Tuesday
        hour = now.hour
        if (day == 1 and hour > 15 and hour < 18):
            await self.bot.change_presence(activity=discord.Game('Golf It!'))
            return

        randomActivity = random.randint(0, 1)
        newActivity = botSettings.GetRandomActivity()

        activity = None
        # Do nothing half of the time
        if (randomActivity == 1 and newActivity is not None):
            newActivity.IncrementUse()
            # Pick a game!
            if (newActivity.type == 0):
                activity = discord.Game(newActivity.name)
            # Pick something to watch
            elif (newActivity.type == 1):
                activity = discord.Activity(name=newActivity.name, type=discord.ActivityType.watching)
            # Pick something to listen to
            elif (newActivity.type == 2):
                activity = discord.Activity(name=newActivity.name, type=discord.ActivityType.listening)

        await self.bot.change_presence(activity=activity)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.guild is None:
            return

        if not message.mention_everyone and self.bot.user.mentioned_in(message):
            selectedQuip = botSettings.GetRandomQuip(message.author)
            if (selectedQuip is not None):
                selectedQuip.IncrementUse()

                response = selectedQuip.quip
                if (selectedQuip.type == QuipType.GUILD_EMOJI.value):
                    response = str(discord.utils.get(message.guild.emojis, name=selectedQuip.quip))

                await message.channel.send(response)
        elif 'jpp' in message.content.lower() and not message.content.startswith('!jpp'):
            await message.add_reaction(str(discord.utils.get(message.guild.emojis, name='jpp')))
        elif '👀' in message.content:
            await message.add_reaction('👀')
        elif 'golf' in message.content.lower() and not message.content.startswith('!golfit'):
            await message.add_reaction('⛳')

    @commands.Cog.listener()
    async def on_ready(self):
        print('We have logged in as {0.user}'.format(self.bot))
        await botSettings.InitSettings(self.bot)
        self.OnUpdateStatus.start()

    @GuildCommand(name='jpp')
    async def OnJPP(self, interaction:discord.Interaction):
        """jpp"""

        emoji = discord.utils.get(interaction.guild.emojis, name='jpp')
        await interaction.response.send_message(str(emoji))

    @GuildCommand(name='golfit')
    async def OnGolfIt(self, interaction:discord.Interaction):
        """For all your golf it music needs"""
        await interaction.response.send_message('https://www.youtube.com/watch?v=KtmGzvBjAYU')

    @GuildCommand(name='whendoesbeauloplay')
    async def OnWhenDoesBeauloPlay(self, interaction:discord.Interaction):
        """👀"""
        await interaction.response.send_message(':eyes: https://www.twitch.tv/beaulo')
    
    @GuildCommand(name='register', description='Allows a user to register with the bot')
    @IsValidChannel(ChannelType.REGISTER)
    async def OnRegisterPlayer(self, interaction:discord.Interaction, name:str=''):
        """Allows a user to register with the bot. This enables matchmaking functionality for that user.

           **string:** <name> (Optional)
           The name you want to use with the bot. Spaces and special characters are allowed.
        """
        if name == '':
            name = interaction.user.nick if interaction.user.nick else interaction.user.name

        print('User {0.user} is registering with name {1}'.format(interaction, name))
    
        if (botSettings.registeredRole is None):
            raise RegisteredRoleUnitialized()

        if (botSettings.IsUserRegistered(interaction.user)):
            raise UserAlreadyRegistered(interaction.user)

        try:
            await interaction.user.add_roles(botSettings.registeredRole, reason='User {0.name} used the register command'.format(interaction.user))

            botSettings.RegisterUser(interaction.user, name)

            await SendMessage(interaction, description='You have been registered as `{}`!'.format(name), color=discord.Color.blue())
        except discord.HTTPException:
            await SendMessage(interaction, description='Registration failed. Please try again.', color=discord.Color.red())

    @GuildCommand(name='setname')
    async def OnSetName(self, interaction:discord.Interaction, name:str):
        """Change your name with the bot
        
           **string:** <name>
           The name you want to use with the bot. Spaces and special characters are allowed.
        """
        print('User {0.user} is changing their name to {1}'.format(interaction, name))

        if (not botSettings.IsUserRegistered(interaction.user)):
            raise UserNotRegistered(interaction.user)

        botSettings.ChangeName(interaction.user, name)

        await SendMessage(interaction, description='Your name has been changed to `{}`'.format(name), color=discord.Color.blue())

    @GuildCommand(name='join')
    @IsValidChannel(ChannelType.LOBBY)
    async def OnJoinQueue(self, interaction:discord.Interaction):
        """Join the matchmaking queue"""
        print('User {0.user} is joining queue.'.format(interaction))

        if (not botSettings.IsUserRegistered(interaction.user)):
            raise UserNotRegistered(interaction.user)

        if (matchService.IsPlayerQueued(interaction.user)):
            raise PlayerAlreadyQueued(interaction.user)

        await matchService.JoinQueue(interaction, interaction.user)

    @GuildCommand(name='leave')
    @IsValidChannel(ChannelType.LOBBY)
    async def OnLeaveQueue(self, interaction:discord.Interaction):
        """Leave the matchmaking queue"""
        print('User {0.user} is leaving queue.'.format(interaction))

        if (not botSettings.IsUserRegistered(interaction.user)):
            raise UserNotRegistered(interaction.user)

        if (not matchService.IsPlayerQueued(interaction.user)):
            raise PlayerNotQueued(interaction.user)

        await matchService.LeaveQueue(interaction, interaction.user)

    @GuildCommand(name='queue')
    @IsValidChannel(ChannelType.LOBBY)
    async def OnShowQueue(self, interaction:discord.Interaction):
        """Show the matchmaking queue"""
        print('Showing queue')

        await matchService.ShowQueue(interaction)

    @GuildCommand(name='missing')
    @IsValidChannel(ChannelType.LOBBY)
    async def OnShowMissingPlayers(self, interaction:discord.Interaction):
        """Shows who is not in the matchmaking queue"""
        print('Showing missing players')

        if (botSettings.guild is None):
            raise InvalidGuild()

        missingMembers = []
        for channel in botSettings.guild.voice_channels:
            missingMembers.extend(matchService.GetNotInQueue(channel.voice_states))

        if (len(missingMembers) == 0):
            await SendMessage(interaction, description='Nobody is missing from queue.', color=discord.Color.blue())
            return

        field = {}
        field['name'] = 'Players not in queue'
        field['value'] = ''
        field['inline'] = False

        for memberID in missingMembers:
            try:
                member = await botSettings.guild.fetch_member(str(memberID))
                field['value'] += '{0.mention}\n'.format(member)
            except (discord.NotFound, discord.HTTPException, discord.Forbidden):
                field['value'] += '{0}\n'.format(memberID)

        await SendMessage(interaction, fields=[field], color=discord.Color.blue())

    @GuildCommand(name='ranks')
    @app_commands.describe(broadcast='Whether or not to broadcast your stats for everyone to see.')
    async def OnShowRanks(self, interaction:discord.Interaction, broadcast:bool = True):
        """Shows the ranks
        
           **bool:** <broadcast>
           Whether or not to broadcast your stats for everyone to see.
        """
        print('Showing ranks')

        roles = botSettings.GetSortedMMRRoles()
        fields = []

        for role in roles:
            field = {}
            field['name'] = '{0.name}'.format(role.role)
            field['value'] = 'Role: {0.mention}\nMMR Range: {1}-{2}\nMMR Delta: +-{3}'.format(role.role, role.mmrMin, role.mmrMax, role.mmrDelta)
            field['inline'] = False
            fields.append(field)

        if (len(fields) == 0):
            await SendMessage(interaction, description='There are currently no ranks.', ephemeral=(not broadcast), color=discord.Color.blue())
        else:
            await SendMessage(interaction, fields=fields, ephemeral=(not broadcast), color=discord.Color.blue())

    @GuildCommand(name='maps')
    @app_commands.describe(broadcast='Whether or not to broadcast your stats for everyone to see.')
    async def OnShowMaps(self, interaction:discord.Interaction, broadcast:bool = True):
        """Shows the maps
        
           **bool:** <broadcast>
           Whether or not to broadcast your stats for everyone to see.
        """
        print('Showing maps')

        maps = botSettings.GetSortedMaps()
        fields = []

        for _map in maps:
            field = {}
            field['name'] = '{}'.format(_map.name)
            field['value'] = 'Times Played: {}'.format(_map.timesPlayed)
            field['inline'] = True 
            fields.append(field)

        numMaps = len(maps)
        footer = '{} map{}'.format(numMaps, '' if numMaps == 1 else 's')

        if (len(fields) == 0):
            await SendMessage(interaction, description='There are currently no maps.', ephemeral=(not broadcast), color=discord.Color.blue())
        else:
            await SendMessage(interaction, fields=fields, footer=footer, ephemeral=(not broadcast), color=discord.Color.blue())

    @GuildCommand(name='pools')
    @app_commands.describe(broadcast='Whether or not to broadcast your stats for everyone to see.')
    async def OnShowMapPools(self, interaction:discord.Interaction, broadcast:bool = True):
        """Shows the map pools
        
           **bool:** <broadcast>
           Whether or not to broadcast your stats for everyone to see.
        """

        pools = botSettings.GetSortedMapPools()
        fields = []

        for pool in pools:
            customStr = ''
            if (pool.type == MapPoolType.CUSTOM.value):
                customStr = 'Type: Custom\n'
            elif (pool.type == MapPoolType.EXCLUDE.value):
                customStr = 'Type: Exclude\n'

            field = {}
            field['name'] = '{}'.format(pool.name)
            field['value'] = 'Times Played: {}\n{}Maps: {}'.format(pool.timesPlayed, customStr, pool.GetMapNames())
            field['inline'] = True 
            fields.append(field)

        numPools = len(pools)
        footer = '{} map pool{}'.format(numPools, '' if numPools == 1 else 's')

        if (len(fields) == 0):
            await SendMessage(interaction, description='There are currently no map pools.', ephemeral=(not broadcast), color=discord.Color.blue())
        else:
            currentPool = 'None' if botSettings.currentPool is None else botSettings.currentPool
            await SendMessage(interaction, description='The current map pool is: `{}`'.format(currentPool), fields=fields, footer=footer, ephemeral=(not broadcast), color=discord.Color.blue())

    @GuildCommand(name='addstrat')
    @IsActivePlayer()
    @app_commands.describe(strat_type='The type of strat you want to have.', title='The name of the strat you want to add.', strat='The strat you want to add.')
    @app_commands.choices(strat_type=[
        Choice(name='Attack', value=StratRouletteTeamType.ATTACKER.value),
        Choice(name='Defense', value=StratRouletteTeamType.DEFENDER.value),
        Choice(name='Both', value=StratRouletteTeamType.BOTH.value) ])
    async def OnAddStratRouletteStrat(self, interaction:discord.Interaction, strat_type:Choice[int], title:str, strat:str):
        """Adds a strat to the Strat Roulette pool

           **string|int:** <type>
           The type of strat you want to have.
           Available results (not case sensitive):
           - 0 (Attack)
           - 1 (Defense)
           - 2 (Both)
           - attack (Attack)
           - a (Attack)
           - defense (Defense)
           - d (Defense)
           - both (Both)
           - b (Both)

           **string:** <title>
           The name of the strat you want to add. If you want multiple words, surround them with double quotes "like this".

           **string:** <strat>
           The strat you want to add. No quotes needed.
        """
        type = await StratRouletteTeamType.convert(strat_type.value)

        if (type == StratRouletteTeamType.INVALID):
            raise InvalidStratRouletteTeamType(type)

        botSettings.AddStratRouletteStrat(type.value, title, strat)
        message = '[{}] Strat Added `[{}] {}`'.format(type.name, title, strat)
        await SendMessage(interaction, description=message, color=discord.Color.blue())

    @GuildCommand(name='strats')
    async def OnShowStratRouletteStrats(self, interaction:discord.Interaction):
        """Shows the Strat Roulette strats available"""

        if (len(botSettings.strats) == 0):
            raise NoStratRouletteStrats()

        messages = []
        fields = []
        heading = 'Strat Roulette Strats'

        def CreateField():
            field = {}
            field['name'] = heading
            field['value'] = ''
            field['inline'] = False 

            return field

        field = CreateField() 

        message = ''
        currentMessageSize = 0
        index = 0
        numPages = 0
        attackerStrats = 0
        defenderStrats = 0
        bothStrats = 0
        for strat in botSettings.strats:
            type = await StratRouletteTeamType.convert(strat.type)

            if (type == StratRouletteTeamType.ATTACKER):
                attackerStrats += 1
            elif (type == StratRouletteTeamType.DEFENDER):
                defenderStrats += 1
            elif (type == StratRouletteTeamType.BOTH):
                bothStrats += 1

            newText = '{}. [{}] `[{}] {}\n`'.format(index, type.name, strat.title, strat.strat)

            # Intentionally stopping short of the 6000 character limit since
            # the limit is encompassing the entire embed.
            # This gives the message wiggle room to guarantee it doesn't pass
            # the limit.
            if (currentMessageSize + len(newText) > 5500):
                field['value'] += message
                fields.append(field)
                field = CreateField()
                message = ''
                messages.append(fields)
                fields = []
                currentMessageSize = 0
                numPages += 1

            if (len(message) + len(newText) > 1024):
                field['value'] += message
                fields.append(field)
                field = CreateField()
                message = ''
                numPages += 1

            message += newText
            currentMessageSize += len(newText)
            index += 1

        field['value'] += message
        fields.append(field)
        numPages += 1

        messages.append(fields)

        if (numPages > 1):
            page = 0
            for _message in messages:
                for field in _message:
                    page += 1
                    field['name'] = '{}{}'.format(heading, ' [{}/{}]'.format(page, numPages))

        footerStr = '{} strats available. {} Attacker, {} Defender, {} Both'.format(index, attackerStrats, defenderStrats, bothStrats)
        await SendMessages(interaction, messages, footer=footerStr, color=discord.Color.blue())

    @GuildCommand(name='stats')
    @app_commands.describe(broadcast='Whether or not to broadcast your stats for everyone to see.')
    async def OnShowStats(self, interaction:discord.Interaction, broadcast:bool = True):
        """Shows your stats

           **bool:** <broadcast>
           Whether or not to broadcast your stats for everyone to see.
        """
        print('Showing stats for {}'.format(interaction.user))

        if (not botSettings.IsUserRegistered(interaction.user)):
            raise UserNotRegistered(interaction.user)

        player = botSettings.GetRegisteredPlayerByID(interaction.user.id)
        prevRole, currentRole = botSettings.GetMMRRole(interaction.user)

        class DummyObject(object) : pass

        results = {}
        players = {}

        def AddMapWin(map:str):
            if (map not in results):
                dummy = DummyObject()
                dummy.wins = 1
                dummy.loses = 0
                dummy.name = map
                results[map] = dummy
            else:
                results[map].wins += 1

        def AddMapLoss(map:str):
            if (map not in results):
                dummy = DummyObject()
                dummy.wins = 0
                dummy.loses = 1
                dummy.name = map
                results[map] = dummy
            else:
                results[map].loses += 1

        def RegisterPlayer(player:int):
            if (player not in players):
                dummy = DummyObject()
                dummy.winsWith = 0
                dummy.lossesWith = 0
                dummy.winsAgainst = 0
                dummy.lossesAgainst = 0
                dummy.id = player
                players[player] = dummy

        def AddPlayerStats(myTeam, enemyTeam, isWin):
            for player in myTeam:
                RegisterPlayer(player._id)

                if isWin:
                    players[player._id].winsWith += 1
                else:
                    players[player._id].lossesWith += 1

            for player in enemyTeam:
                RegisterPlayer(player._id)

                if isWin:
                    players[player._id].winsAgainst += 1
                else:
                    players[player._id].lossesAgainst += 1


            #if (player in winningTeam):
                #players[player].

        # TODO: Calculate how many times we played with each player so we can do player stats

        team1Matches = MatchHistoryData.objects(_team1__match={'_id':interaction.user.id}) 
        team2Matches = MatchHistoryData.objects(_team2__match={'_id':interaction.user.id})

        def CheckResults(matches, winResult, loseResult):
            for data in matches:
                if (data._result == MatchResult.CANCELLED.value):
                    continue

                if (winResult == MatchResult.TEAM1VICTORY.value):
                    AddPlayerStats(data._team1, data._team2, (data._result == winResult))
                elif (winResult == MatchResult.TEAM2VICTORY.value):
                    AddPlayerStats(data._team2, data._team1, (data._result == winResult))

                if (data._result == winResult):
                    AddMapWin(data._map)
                elif (data._result == loseResult):
                    AddMapLoss(data._map)

        CheckResults(team1Matches, MatchResult.TEAM1VICTORY.value, MatchResult.TEAM2VICTORY.value)
        CheckResults(team2Matches, MatchResult.TEAM2VICTORY.value, MatchResult.TEAM1VICTORY.value)	

        title = 'Stats for {}'.format(player.name)

        mmrField = {}
        mmrField['name'] = 'MMR'
        mmrField['inline'] = True

        mmrField['value'] = '**Rank:** {0.mention}\n'.format(currentRole.role)
        mmrField['value'] += '**MMR:** {}\n'.format(player.mmr)
        mmrField['value'] += '**Highest MMR:** {}\n'.format(player.highestMMR)
        mmrField['value'] += '**Lowest MMR:** {}\n'.format(player.lowestMMR)

        winLossDelta = player.wins - player.loses
        winLossPercent = player.wins / (1 if player.matchesPlayed == 0 else player.matchesPlayed)
        wlDelta = '{}{}'.format('+' if winLossDelta >= 0 else '-', abs(winLossDelta))

        matchField = {}
        matchField['name'] = 'Match History'
        matchField['inline'] = True

        matchField['value'] = '**Matches Played:** {}\n'.format(player.matchesPlayed)
        matchField['value'] += '**Win/Loss:** {}/{} ({}, {:.2f}%)\n'.format(player.wins, player.loses, wlDelta, winLossPercent * 100)

        streakName, streakValue = player.GetStreak()

        matchField['value'] += '**Current Streak:** {} {}\n'.format(streakName, streakValue)
        matchField['value'] += '**Best Win Streak:** {}\n'.format(player.highestWinStreak)
        matchField['value'] += '**Worst Lose Streak:** {}\n'.format(player.highestLoseStreak)

        bestMaps = sorted(results.values(), key=lambda map : map.wins, reverse=True)
        worstMaps = sorted(results.values(), key=lambda map : map.loses, reverse=True)
        mostPlayedMaps = sorted(results.values(), key=lambda map : map.wins + map.loses, reverse=True)

        bestMap = bestMaps[0] if len(bestMaps) > 0 else None
        worstMap = worstMaps[0] if len(worstMaps) > 0 else None
        mostPlayedMap = mostPlayedMaps[0] if len(mostPlayedMaps) > 0 else None
        leastPlayedMap = mostPlayedMaps[-1] if len(mostPlayedMaps) > 0 else None

        mapField = {}
        mapField['name'] = 'Map History'
        mapField['value'] = ''
        mapField['inline'] = True

        if (mostPlayedMap is not None):
            numPlayed = mostPlayedMap.wins + mostPlayedMap.loses
            mapField['value'] += '**Most Played Map:** {} ({})\n'.format(mostPlayedMap.name, numPlayed)

        if (leastPlayedMap is not None):
            numPlayed = leastPlayedMap.wins + leastPlayedMap.loses
            mapField['value'] += '**Least Played Map:** {} ({})\n'.format(leastPlayedMap.name, numPlayed)

        if (bestMap is not None):
            bestMapDelta = bestMap.wins - bestMap.loses
            numPlayed = bestMap.wins + bestMap.loses
            bestMapWinLossPercent = bestMap.wins / (1 if numPlayed == 0 else numPlayed)
            bmDelta = '{}{}'.format('+' if bestMapDelta >= 0 else '-', abs(bestMapDelta))
            mapField['value'] += '**Best Map:** {} ({}, {:.2f}%)\n'.format(bestMap.name, bmDelta, bestMapWinLossPercent * 100)

        if (worstMap is not None):
            worstMapDelta = worstMap.wins - worstMap.loses
            numPlayed = worstMap.wins + worstMap.loses
            worstMapWinLossPercent = worstMap.wins / (1 if numPlayed == 0 else numPlayed)
            wmDelta = '{}{}'.format('+' if worstMapDelta >= 0 else '-', abs(worstMapDelta))
            mapField['value'] += '**Worst Map:** {} ({}, {:.2f}%)'.format(worstMap.name, wmDelta, worstMapWinLossPercent * 100)

        # We dont want data about ourself messing with the results
        if interaction.user.id in players:
            del players[interaction.user.id]

        mostPlayedPlayers = sorted(players.values(), key=lambda player: player.winsWith + player.lossesWith, reverse=True)
        bestPlayers = sorted(players.values(), key=lambda player: player.winsWith, reverse=True)
        worstPlayers = sorted(players.values(), key=lambda player: player.lossesWith, reverse=True)
        rivalPlayers = sorted(players.values(), key=lambda player: player.lossesAgainst, reverse=True)

        mostPlayedPlayer = mostPlayedPlayers[0] if len(mostPlayedPlayers) > 0 else None
        leastPlayedPlayer = mostPlayedPlayers[-1] if len(mostPlayedPlayers) > 0 else None
        bestPlayer = bestPlayers[0] if len(bestPlayers) > 0 else None
        worstPlayer = worstPlayers[0] if len(worstPlayers) > 0 else None
        rivalPlayer = rivalPlayers[0] if len(rivalPlayers) > 0 else None

        playerField = {}
        playerField['name'] = 'Player History'
        playerField['value'] = ''
        playerField['inline'] = True

        if (mostPlayedPlayer is not None):
            numPlayed = mostPlayedPlayer.winsWith + mostPlayedPlayer.lossesWith
            playerField['value'] += '**Played with most:** {} ({} times)\n'.format(botSettings.GetUserNameByID(mostPlayedPlayer.id), numPlayed)

        if (leastPlayedPlayer is not None):
            numPlayed = leastPlayedPlayer.winsWith + leastPlayedPlayer.lossesWith
            playerField['value'] += '**Played with least:** {} ({} times)\n'.format(botSettings.GetUserNameByID(leastPlayedPlayer.id), numPlayed)
            
        if (bestPlayer is not None):
            numPlayed = bestPlayer.winsWith
            playerField['value'] += '**Carried by:** {} ({} wins with)\n'.format(botSettings.GetUserNameByID(bestPlayer.id), numPlayed)

        if (worstPlayer is not None):
            numPlayed = worstPlayer.lossesWith
            playerField['value'] += '**Sabotaged by:** {} ({} losses with)\n'.format(botSettings.GetUserNameByID(worstPlayer.id), numPlayed)

        if (rivalPlayer is not None):
            numPlayed = rivalPlayer.lossesAgainst
            playerField['value'] += '**Rival:** {} ({} losses to)\n'.format(botSettings.GetUserNameByID(rivalPlayer.id), numPlayed)

        await SendMessage(interaction, title=title, fields=[mmrField, matchField, mapField, playerField], ephemeral=(not broadcast), color=discord.Color.blue())

    @GuildCommand(name='slap')
    @app_commands.describe(member='The person you wish to slap.')
    async def OnSlapUser(self, interaction:discord.Interaction, member:discord.Member):
        """Slaps the user, preferably with a trout

           **discord.Member:** <member>
           The person you wish to slap.
        """

        quips = ['On it boss!', '*Trout incoming*', 'Somebody call an ambulance... but not for me!', 'Salmon cannons are overrated, trout cannon when?', 'You might want to get some ice']

        # Acknowledge the command
        await interaction.response.send_message(random.choice(quips), ephemeral=True)

        # Send the slap!
        await interaction.channel.send('{0.mention} slaps {1.mention} around a bit with a large trout'.format(interaction.user, member))

    @GuildCommand(name='rules')
    async def OnShowRules(self, interaction:discord.Interaction):
        """Shows the rules of conduct
        """

        rules=['Respect your JPPeers', 'Gab should download the build', 'Dont join the lobby before 15h45 *\*cough\* Simon \*cough\**', 'Ban Clash and Oryx', 'Click Heads', 'Love Fort Boyard', 'Please leave the lobby.... pleassssseeeee']

        field = {}
        field['name'] = 'Rules of JPP' 
        field['value'] = ''
        field['inline'] = False 

        for rule in rules:
            field['value'] += '- {}\n'.format(rule)

        await SendMessage(interaction, fields=[field], color=discord.Color.blue())

    @OnUpdateStatus.error
    async def errorHandling(self, ctx, error):
        await HandleError(ctx, error)

    @OnShowRules.error
    @OnSlapUser.error
    @OnShowStratRouletteStrats.error
    @OnAddStratRouletteStrat.error
    @OnShowStats.error
    @OnShowRanks.error
    @OnShowMissingPlayers.error
    @OnJoinQueue.error
    @OnLeaveQueue.error
    @OnShowQueue.error
    @OnSetName.error
    @OnRegisterPlayer.error
    @OnJPP.error
    @OnWhenDoesBeauloPlay.error
    @OnGolfIt.error
    @OnShowMapPools.error
    @OnShowMaps.error
    async def errorHandling2(self, interaction:discord.Interaction, error:app_commands.AppCommandError):
        await HandleAppError(interaction, error)
