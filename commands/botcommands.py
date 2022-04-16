from data.botsettings import ChannelType, RegisteredRoleUnitialized, InvalidGuild, EmptyName
from data.playerdata import UserNotRegistered, UserAlreadyRegistered
from data.matchhistorydata import MatchHistoryData, MatchResult
from data.quipdata import QuipType
from data.mappool import MapPoolType
from services.matchservice import PlayerAlreadyQueued, PlayerNotQueued
from utils.chatutils import SendMessage
from utils.botutils import IsValidChannel
from utils.errorutils import HandleError
from globals import *
from discord.ext import commands, tasks
from datetime import datetime
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

    @commands.command(name='jpp')
    async def OnJPP(self, ctx):
        """jpp"""

        emoji = discord.utils.get(ctx.guild.emojis, name='jpp')
        await ctx.send(str(emoji))

    @commands.command(name='golfit')
    async def OnGolfIt(self, ctx):
        """For all your golf it music needs"""
        await ctx.send('https://www.youtube.com/watch?v=KtmGzvBjAYU')

    @commands.command(name='whendoesbeauloplay')
    async def OnWhenDoesBeauloPlay(self, ctx):
        """👀"""
        await ctx.send(':eyes: https://www.twitch.tv/beaulo')
    
    @commands.command(name='register', aliases=['r'], brief='Allows a user to register with the bot')
    @IsValidChannel(ChannelType.REGISTER)
    async def OnRegisterPlayer(self, ctx, *name):
        """Allows a user to register with the bot. This enables matchmaking functionality for that user.

           **string:** <name>
           The name you want to use with the bot. Spaces and special characters are allowed.
        """
        if (len(name) == 0):
            raise EmptyName()

        combinedName = ' '.join(name)
        print('User {0.author} is registering with name {1}'.format(ctx, combinedName))
    
        if (botSettings.registeredRole is None):
            raise RegisteredRoleUnitialized()

        if (botSettings.IsUserRegistered(ctx.author)):
            raise UserAlreadyRegistered(ctx.author)

        try:
            await ctx.author.add_roles(botSettings.registeredRole, reason='User {0.name} used the register command'.format(ctx.author))

            botSettings.RegisterUser(ctx.author, combinedName)

            await SendMessage(ctx, description='You have been registered as `{}`!'.format(combinedName), color=discord.Color.blue())
        except discord.HTTPException:
            await SendMessage(ctx, description='Registration failed. Please try again.', color=discord.Color.red())

    @commands.command(name='setname')
    async def OnSetName(self, ctx, *name):
        """Change your name with the bot
        
           **string:** <name>
           The name you want to use with the bot. Spaces and special characters are allowed.
        """
        if (len(name) == 0):
            raise EmptyName()

        combinedName = ' '.join(name)
        print('User {0.author} is changing their name to {1}'.format(ctx, combinedName))

        if (not botSettings.IsUserRegistered(ctx.author)):
            raise UserNotRegistered(ctx.author)

        botSettings.ChangeName(ctx.author, combinedName)

        await SendMessage(ctx, description='Your name has been changed to `{}`'.format(combinedName), color=discord.Color.blue())

    @commands.command(name='join', aliases=['j'])
    @IsValidChannel(ChannelType.LOBBY)
    async def OnJoinQueue(self, ctx):
        """Join the matchmaking queue"""
        print('User {0.author} is joining queue.'.format(ctx))

        if (not botSettings.IsUserRegistered(ctx.author)):
            raise UserNotRegistered(ctx.author)

        if (matchService.IsPlayerQueued(ctx.author)):
            raise PlayerAlreadyQueued(ctx.author)

        await matchService.JoinQueue(ctx, ctx.author)

    @commands.command(name='leave', aliases=['l'])
    @IsValidChannel(ChannelType.LOBBY)
    async def OnLeaveQueue(self, ctx):
        """Leave the matchmaking queue"""
        print('User {0.author} is leaving queue.'.format(ctx))

        if (not botSettings.IsUserRegistered(ctx.author)):
            raise UserNotRegistered(ctx.author)

        if (not matchService.IsPlayerQueued(ctx.author)):
            raise PlayerNotQueued(ctx.author)

        await matchService.LeaveQueue(ctx, ctx.author)

    @commands.command(name='queue')
    @IsValidChannel(ChannelType.LOBBY)
    async def OnShowQueue(self, ctx):
        """Show the matchmaking queue"""
        print('Showing queue')

        await matchService.ShowQueue(ctx)

    @commands.command(name='missing')
    @IsValidChannel(ChannelType.LOBBY)
    async def OnShowMissingPlayers(self, ctx):
        """Shows who is not in the matchmaking queue"""
        print('Showing missing players')

        if (botSettings.guild is None):
            raise InvalidGuild()

        missingMembers = []
        for channel in botSettings.guild.voice_channels:
            missingMembers.extend(matchService.GetNotInQueue(channel.voice_states))

        if (len(missingMembers) == 0):
            await SendMessage(ctx, description='Nobody is missing from queue.', color=discord.Color.blue())
            return

        field = {}
        field['name'] = 'Players not in queue'
        field['value'] = ''
        field['inline'] = False

        converter = commands.MemberConverter() 

        for memberID in missingMembers:
            try:
                member = await converter.convert(ctx, str(memberID))
                field['value'] += '{0.mention}\n'.format(member)
            except commands.errors.MemberNotFound:
                field['value'] += '{0}\n'.format(memberID)

        await SendMessage(ctx, fields=[field], color=discord.Color.blue())

    @commands.command(name='ranks')
    async def OnShowRanks(self, ctx):
        """Shows the ranks"""
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
            await SendMessage(ctx, description='There are currently no ranks.', color=discord.Color.blue())
        else:
            await SendMessage(ctx, fields=fields, color=discord.Color.blue())

    @commands.command(name='maps')
    async def OnShowMaps(self, ctx):
        """Shows the maps"""
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
            await SendMessage(ctx, description='There are currently no maps.', color=discord.Color.blue())
        else:
            await SendMessage(ctx, fields=fields, footer=footer, color=discord.Color.blue())

    @commands.command(name='pools')
    async def OnShowMapPools(self, ctx):
        """Shows the map pools"""

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
            await SendMessage(ctx, description='There are currently no map pools.', color=discord.Color.blue())
        else:
            await SendMessage(ctx, fields=fields, footer=footer, color=discord.Color.blue())

    @commands.command(name='stats')
    async def OnShowStats(self, ctx):
        """Shows your stats"""
        print('Showing stats for {}'.format(ctx.author))

        if (not botSettings.IsUserRegistered(ctx.author)):
            raise UserNotRegistered(ctx.author)

        player = botSettings.GetRegisteredPlayerByID(ctx.author.id)
        prevRole, currentRole = botSettings.GetMMRRole(ctx.author)

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

        team1Matches = MatchHistoryData.objects(_team1__match={'_id':ctx.author.id}) 
        team2Matches = MatchHistoryData.objects(_team2__match={'_id':ctx.author.id})

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
        if ctx.author.id in players:
            del players[ctx.author.id]

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

        await SendMessage(ctx, title=title, fields=[mmrField, matchField, mapField, playerField], color=discord.Color.blue())

    @commands.command(name='slap')
    async def OnSlapUser(self, ctx, member:discord.Member):
        """Slaps the user, preferably with a trout

           **discord.Member:** <member>
           The person you wish you slap.
        """

        # First send the slap
        await ctx.channel.send('{0.mention} slaps {1.mention} around a bit with a large trout'.format(ctx.author, member))

        # Then clean up the request to avoid polluting chat
        try:
            await ctx.message.delete()
        except:
            pass

    @OnJPP.error
    @OnWhenDoesBeauloPlay.error
    @OnRegisterPlayer.error
    @OnSetName.error
    @OnJoinQueue.error
    @OnLeaveQueue.error
    @OnShowQueue.error
    @OnShowMissingPlayers.error
    @OnShowRanks.error
    @OnShowMaps.error
    @OnShowStats.error
    @OnGolfIt.error
    @OnUpdateStatus.error
    @OnSlapUser.error
    @OnShowMapPools.error
    async def errorHandling(self, ctx, error):
        await HandleError(ctx, error)
