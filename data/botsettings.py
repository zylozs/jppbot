from data.playerdata import PlayerData
from data.mmrrole import MMRRole 
from data.matchhistorydata import MatchHistoryData
from data.mappool import MapPool, MapPoolType
from services.matchservice import TeamResult, FakeUser
from data.siegemap import SiegeMap
from data.activitydata import ActivityData
from data.quipdata import QuipData, QuipType
from data.stratroulettedata import StratRouletteData
from enum import Enum
from discord.ext import commands
from mongoengine import Document, IntField, StringField
from discord import app_commands
import discord
import random
import math

class ChannelTypeInvalid(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('Channel Type "{}" is not valid.'.format(argument))

class RegisteredRoleUnitialized(app_commands.AppCommandError):
    def __init__(self):
        super().__init__('The registered role has not been setup.')

class AdminRoleUnitialized(app_commands.AppCommandError):
    def __init__(self):
        super().__init__('The admin role has not been setup.')

class UserNotAdmin(app_commands.CheckFailure):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('The user {0.mention} is not an admin'.format(argument))

class UserNotOwner(commands.CheckFailure):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('The user {0.mention} is not the owner'.format(argument))

class UserNotActive(app_commands.CheckFailure):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('The user {0.mention} is not active enough.'.format(argument))

class GuildTextChannelMismatch(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('Text Channel "{0.mention}" is not in the same guild as the other text channels.'.format(argument))

class GuildRoleMismatch(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('Role {0.mention}" is not in the same guild as the text channels.'.format(argument))

class InvalidRole(commands.BadArgument):
    def __init__(self):
        super().__init__('`@everyone` is not a valid role.')

class InvalidGuild(commands.BadArgument):
    def __init__(self):
        super().__init__('There is no guild set.')

class InvalidCommandChannel(app_commands.CheckFailure):
    def __init__(self, argument, type):
        self.argument = argument
        self.type = type
        super().__init__('{0} is not the correct channel for {1.value} commands'.format(argument.mention if hasattr(argument, 'mention') else 'This', type))

class InvalidOwnerCommandChannel(commands.CheckFailure):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('{0.mention} is not the correct channel for owner commands'.format(argument))

class EmptyName(commands.BadArgument):
    def __init__(self):
        super().__init__('An empty string is not a valid name.')

class EmptyQuip(commands.BadArgument):
    def __init__(self):
        super().__init__('An empty string is not a valid quip.')

class InvalidActivityIndex(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('{0} is not a valid activity index.'.format(argument))

class InvalidQuipIndex(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('{0} is not a valid quip index.'.format(argument))

class InvalidStratIndex(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('{0} is not a valid Strat Roulette strat index.'.format(argument))

class InvalidChannelType(commands.BadArgument):
    def __init__(self):
        super().__init__('INVALID is not a valid channel type.')

class ChannelType(Enum):
    LOBBY = "lobby"
    RESULTS = "result"
    ADMIN = "admin"
    REGISTER = "register"
    REPORT = "report"
    INVALID = "invalid"

    @classmethod
    async def convert(cls, argument):
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
        elif (tempArg.__contains__(ChannelType.REPORT.value)):
            returnType = ChannelType.REPORT

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
    _reportChannel = IntField(default=-1)
    _registeredRole = IntField(default=-1)
    _adminRole = IntField(default=-1)
    _nextUniqueMatchID = IntField(default=0)
    _currentPool = StringField(default='')

    # Settings
    guild = None # discord.Guild
    lobbyChannel = None # discord.TextChannel
    resultsChannel = None # discord.TextChannel
    adminChannel = None # discord.TextChannel
    registerChannel = None # discord.TextChannel
    reportChannel = None # discord.TextChannel
    registeredRole = None # discord.Role
    adminRole = None # discord.Role

    registeredPlayers = {}
    mmrRoles = {}
    maps = {}
    pools = {}
    currentPool = None
    activities = []
    quips = []
    strats = []

    def _GetGuild(self, id, bot):
        if (len(bot.guilds) == 0):
            return None

        return bot.get_guild(id)

    def _GetChannel(self, id):
        if (self.guild is None):
            return None

        # This bot is only intended to work in one guild.  Grab the one that
        # matches our guild id
        return self.guild.get_channel(id)

    def _GetRole(self, id):
        if (self.guild is None):
            return None

        return self.guild.get_role(id)

    async def InitSettings(self, bot):
        # Channels used for various bot functionality
        # Type: discord.TextChannel
        self.guild = self._GetGuild(self._guild, bot)
        self.lobbyChannel = self._GetChannel(self._lobbyChannel)
        self.resultsChannel = self._GetChannel(self._resultsChannel)
        self.adminChannel = self._GetChannel(self._adminChannel)
        self.registerChannel = self._GetChannel(self._registerChannel)
        self.reportChannel = self._GetChannel(self._reportChannel)

        # Player data
        # Type: Dictionary<key=discord.User, value=PlayerData>
        self.registeredPlayers = {}
        
        for player in PlayerData.objects:
            await player.Init(bot)
            self.registeredPlayers[player.GetID()] = player

        self.registeredRole = self._GetRole(self._registeredRole)
        self.adminRole = self._GetRole(self._adminRole)

        # MMR Rank definition
        # Type: Dictionary<key=discord.Role, value=MMRRole>
        self.mmrRoles = {}

        for role in MMRRole.objects:
            role.Init(self.guild)
            self.mmrRoles[role.role.id] = role 

        # Maps
        # Type: Dictionary<key=string, value=SiegeMap>
        self.maps = {}

        for _map in SiegeMap.objects:
            _map.Init()
            self.maps[_map.name.lower()] = _map

        # Pools
        # Type: Dictionary<key=string, value=MapPool>
        self.pools = {}

        for pool in MapPool.objects:
            pool.Init()
            self.pools[pool.name.lower()] = pool

        self.currentPool = self._currentPool
        if (not self.DoesMapPoolExist(self.currentPool)):
            self.currentPool = None

        # Activities
        # Type: Array<ActivityData>
        self.activities = []

        for activity in ActivityData.objects:
            activity.Init()
            self.activities.append(activity)

        # Quips
        # Type: Array<QuipData>
        self.quips = []

        for quip in QuipData.objects:
            quip.Init(bot)
            self.quips.append(quip)

        # Strat Roulette Strats
        # Type: Array<StratRouletteData>
        self.strats = []

        for strat in StratRouletteData.objects:
            strat.Init()
            self.strats.append(strat)

        self.strats.sort(key=lambda strat : strat.type)

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
            self.resultsChannel = None
            self._resultsChannel = -1
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

    def RegisterUser(self, user:discord.User, name:str):
        newPlayer = PlayerData()
        newPlayer.SetUser(user, name)
        self.registeredPlayers[user.id] = newPlayer

    def ChangeName(self, user:discord.User, name:str):
        self.registeredPlayers[user.id].SetName(name)

    def AddMMRRole(self, role:discord.Role, mmrMin:int, mmrMax:int, mmrDelta:int):
        newRole = MMRRole()
        newRole.SetData(role, mmrMin, mmrMax, mmrDelta)
        self.mmrRoles[role.id] = newRole 

    def UpdateMMRRole(self, role:discord.Role, mmrMin:int, mmrMax:int, mmrDelta:int):
        self.mmrRoles[role.id].UpdateData(mmrMin, mmrMax, mmrDelta)

    def RemoveMMRRole(self, role:discord.Role):
        self.mmrRoles[role.id].delete() # remove entry from database
        del self.mmrRoles[role.id]

    def AddMap(self, name:str, thumbnailURL:str):
        _map = SiegeMap()
        _map.SetName(name, thumbnailURL)
        self.maps[name.lower()] = _map
    
    def RemoveMap(self, name:str):
        properName = self.GetMapProperName(name)
        self.maps[name.lower()].delete() # remove entry from database
        del self.maps[name.lower()]

        for pool in self.pools.values():
            pool.RemoveMap(properName)

    def SetMapThumbnail(self, name:str, thumbnailURL:str):
        self.maps[name.lower()].SetThumbnail(thumbnailURL)

    def GetMapProperName(self, name:str):
        return self.maps[name.lower()].name

    def GetMapPoolProperName(self, name:str):
        return self.pools[name.lower()].name

    def GetMapThumbnail(self, name:str):
        return self.maps[name.lower()].thumbnailURL

    def AddMapPool(self, name:str, type:int):
        pool = MapPool()
        pool.SetData(name, type)
        self.pools[name.lower()] = pool

    def RemoveMapPool(self, name:str):
        self.pools[name.lower()].delete() # remove entry from database
        del self.pools[name.lower()]

    def AddMapPoolMap(self, poolName:str, mapName:str):
        self.pools[poolName.lower()].AddMap(mapName)

    def RemoveMapPoolMap(self, poolName:str, mapName:str):
        self.pools[poolName.lower()].RemoveMap(mapName)

    def AddStratRouletteStrat(self, type:int, title:str, strat:str):
        newStrat = StratRouletteData()
        newStrat.SetData(type, title, strat)
        self.strats.append(newStrat)
        self.strats.sort(key=lambda _strat : _strat.type)

    def RemoveStratRouletteStrat(self, index:int):
        self.strats[index].delete() # remove entry from database
        self.strats.pop(index)

    def SetMMR(self, user:discord.User, mmr:int):
        return self.SetMMRByID(user.id, mmr)

    def SetMMRByID(self, id:int, mmr:int):
        previousMMR = self.registeredPlayers[id].mmr
        self.registeredPlayers[id].SetMMR(mmr)
        return previousMMR

    def GetMMR(self, user:discord.User):
        return self.GetMMRByID(user.id)

    def GetMMRByID(self, id:int):
        return self.registeredPlayers[id].mmr

    def GetMMRRole(self, user:discord.User, previousMMR:int = -1):
        return self.GetMMRRoleByID(user.id, previousMMR)

    def GetMMRRoleByID(self, id:int, previousMMR:int = -1):
        mmr = self.registeredPlayers[id].mmr
        previousRole = None
        newRole = None

        for role in self.mmrRoles.values():
            if (role.mmrMin <= mmr <= role.mmrMax):
                newRole = role
            if (role.mmrMin <= previousMMR <= role.mmrMax):
                previousRole = role

        return previousRole, newRole

    def GetAllMMRRoles(self):
        roles = []
        for role in self.mmrRoles.values():
            roles.append(role.role)
        return roles

    def IsMMRRoleRangeValid(self, mmrMin, mmrMax):
        for role in self.mmrRoles.values():
            if ((role.mmrMin <= mmrMin <= role.mmrMax) or (role.mmrMin <= mmrMax <= role.mmrMax)):
                return False

        return True

    def GetSortedRegisteredPlayers(self):
        return sorted(self.registeredPlayers.values(), key=lambda player : player.mmr, reverse=True)

    def GetRegisteredPlayerByID(self, id:int):
        return self.registeredPlayers[id]

    def GetTestPlayers(self, num:int):
        testPlayers = []

        class DummyObject(object) : pass

        for i in range(num):
            dummy = DummyObject()
            dummy.name = 'Test Name {}'.format(i)
            dummy.mmr = random.randint(1, 500)
            testPlayers.append(dummy)
        random.shuffle(testPlayers)

        return sorted(testPlayers, key=lambda player : player.mmr, reverse=True)

    def GetSortedMMRRoles(self):
        return sorted(self.mmrRoles.values(), key=lambda role: role.mmrMin)

    def GetSortedMaps(self):
        return sorted(self.maps.values(), key=lambda _map : _map.name.lower())

    def GetSortedMapPools(self):
        return sorted(self.pools.values(), key=lambda pool : pool.name.lower())

    # Union[discord.User, FakeUser] user
    def GetUserName(self, user):
        if (isinstance(user, FakeUser)):
            return user.mention

        return self.GetUserNameByID(user.id)

    def GetUserNameByID(self, id:int):
        # Fake user detected
        if (id < 0):
            return self.GetUserName(FakeUser(id))

        return self.registeredPlayers[id].name

    def IsUserRegistered(self, user:discord.User):
        return self.IsUserRegisteredByID(user.id)

    def IsUserRegisteredByID(self, id:int):
        return id in self.registeredPlayers

    def IsUserAdmin(self, user:discord.User):
        if (isinstance(user, discord.Member)):
            return self.adminRole in user.roles
        else:
            return False

    def IsUserOwner(self, user:discord.User):
        return user.id == 86642208693825536;

    def IsValidMMRRole(self, role:discord.Role):
        return role.id in self.mmrRoles

    def DoesMapExist(self, name:str):
        return name.lower() in self.maps

    def DoesMapPoolExist(self, name:str):
        return name.lower() in self.pools
    
    def DoesMapPoolMapExist(self, poolName:str, mapName:str):
        return mapName in self.pools[poolName.lower()].maps

    def IsValidMapPoolMap(self, poolName:str, mapName:str):
        return self.pools[poolName.lower()].IsValidMap(mapName)

    def IsValidChannel(self, channel:discord.TextChannel, channelType:ChannelType, includeAdmin=True):
        returnType = False
        if (channel is self.lobbyChannel and channelType is ChannelType.LOBBY):
            returnType = True
        elif (channel is self.resultsChannel and channelType is ChannelType.RESULTS):
            returnType = True
        elif (channel is self.adminChannel and channelType is ChannelType.ADMIN):
            returnType = True
        elif (channel is self.registerChannel and channelType is ChannelType.REGISTER):
            returnType = True
        elif (channel is self.reportChannel and channelType is ChannelType.REPORT):
            returnType = True

        if (returnType is False and channel is self.adminChannel and includeAdmin):
            returnType = True

        return returnType 

    def GetNextUniqueMatchID(self):
        id = self._nextUniqueMatchID
        self._nextUniqueMatchID += 1
        self.save()
        return id

    def GetRandomMap(self, selectedPool, enablePMCCOverride = False):
        # sort by times played. Less played maps towards the beginning and more played maps towards the end
        sortedMaps = sorted(self.maps.values(), key=lambda _map : _map.timesPlayed)

        # Remove all maps that aren't in the pool
        if (selectedPool is not None and self.DoesMapPoolExist(selectedPool)):
            pool = self.pools[selectedPool.lower()]

            # Do nothing, we want all maps
            if (pool.type == MapPoolType.ALL.value):
                pass
            else:
                tempMaps = []
                for _map in sortedMaps:
                    if (pool.IsValidMap(_map.name)):
                        tempMaps.append(_map)
                sortedMaps = tempMaps

        # random amongst the least played maps (numMaps / 2)
        numMapsToKeep = int(math.ceil(len(sortedMaps) / 2))

        leastPlayedMaps = sortedMaps[:numMapsToKeep]

        if ('villa' in self.maps and enablePMCCOverride):
            if (self.maps['villa'] not in leastPlayedMaps):
                leastPlayedMaps.append(self.maps['villa'])

        return random.choice(leastPlayedMaps)

    def DeclareMapPlayed(self, mapName:str, poolName):
        if (self.DoesMapExist(mapName)):
            self.maps[mapName.lower()].IncrementTimesPlayed()

        if (poolName is not None and self.DoesMapPoolExist(poolName)):
            self.pools[poolName.lower()].IncrementTimesPlayed()

    # Union[discord.User, FakeUser] user
    def DeclareWinner(self, user, mmrDelta=None):
        # Fake the results for FakeUsers
        if (isinstance(user, FakeUser)):
            return 100, 110, None, None, 10

        return self.DeclareWinnerByID(user.id, mmrDelta)

    def DeclareWinnerByID(self, id:int, mmrDelta=None):
        oldMMR = self.GetMMRByID(id)

        if (mmrDelta == None):
            oldRole, newRole= self.GetMMRRoleByID(id)
            mmrDelta = 0
            if (newRole is not None):
                mmrDelta = newRole.mmrDelta

        self.registeredPlayers[id].UpdateData(mmrDelta, True)

        newMMR = self.GetMMRByID(id)
        oldRole, newRole = self.GetMMRRoleByID(id, oldMMR)

        # Return none if we aren't changing roles
        if (oldRole is not None and oldRole is newRole):
            oldRole = None
            newRole = None

        return oldMMR, newMMR, oldRole, newRole, mmrDelta

    # Union[discord.User, FakeUser] user
    def DeclareLoser(self, user, mmrDelta=None):
        # Fake the results for FakeUsers
        if (isinstance(user, FakeUser)):
            return 100, 90, None, None, 10

        return self.DeclareLoserByID(user.id, mmrDelta)

    def DeclareLoserByID(self, id:int, mmrDelta=None):
        oldMMR = self.GetMMRByID(id)

        if (mmrDelta == None):
            oldRole, newRole= self.GetMMRRoleByID(id)
            mmrDelta = 0
            if (newRole is not None):
                mmrDelta = newRole.mmrDelta

        self.registeredPlayers[id].UpdateData(mmrDelta, False)

        newMMR = self.GetMMRByID(id)
        oldRole, newRole = self.GetMMRRoleByID(id, oldMMR)

        # Return none if we aren't changing roles
        if (oldRole is not None and oldRole is newRole):
            oldRole = None
            newRole = None

        return oldMMR, newMMR, oldRole, newRole, mmrDelta

    # Union[discord.User, FakeUser] user
    def DeclareCancel(self, user):
        # Fake the results for FakeUsers
        if (isinstance(user, FakeUser)):
            return 100, 100, 10

        return self.DeclareCancelByID(user.id)

    def DeclareCancelByID(self, id:int):
        oldRole, newRole= self.GetMMRRoleByID(id)

        oldMMR = self.GetMMRByID(id)
        newMMR = oldMMR

        mmrDelta = 0
        if (newRole is not None):
            mmrDelta = newRole.mmrDelta

        return oldMMR, newMMR, mmrDelta

    # Union[discord.User, FakeUser] user
    def RedoMatch(self, user, oldDelta:int, mmrDelta:int, prevResult:TeamResult, newResult:TeamResult):
        if (isinstance(user, FakeUser)):
            return 100, 110, None, None

        return self.RedoMatchByID(user.id, oldDelta, mmrDelta, prevResult, newResult)

    def RedoMatchByID(self, id:int, oldDelta:int, mmrDelta:int, prevResult:TeamResult, newResult:TeamResult):
        # Fake user detected
        if (id < 0):
            return self.RedoMatch(FakeUser(id), oldDelta, mmrDelta, prevResult, newResult)

        oldMMR = self.GetMMRByID(id)

        self.registeredPlayers[id].RedoData(oldDelta, mmrDelta, prevResult, newResult)

        newMMR = self.GetMMRByID(id)
        oldRole, newRole = self.GetMMRRoleByID(id, oldMMR)

        # Return none if we aren't changing roles
        if (oldRole is not None and oldRole is newRole):
            oldRole = None
            newRole = None

        return oldMMR, newMMR, oldRole, newRole

    def GetRandomActivity(self):
        if (len(self.activities) == 0):
            return None

        return random.choice(self.activities)

    def AddActivity(self, name:str, type:int):
        activity = ActivityData()
        activity.SetData(name, type)
        self.activities.append(activity)

    def RemoveActivity(self, index:int):
        self.activities[index].delete() # remove entry from database
        self.activities.pop(index)

    def GetRandomQuip(self, requestor:discord.User):
        # Filter out responses that can't be given
        def filterPredicate(_quip):
            if (_quip.type == QuipType.SPECIFIC_USER.value):
                if (_quip.user and _quip.user.id == requestor.id):
                    return True
                elif (_quip._user == requestor.id):
                    return True
            
            if (_quip.type == QuipType.GUILD_EMOJI.value and discord.utils.get(self.guild.emojis, name=_quip.quip)):
                return True	

            if (_quip.type == QuipType.REGULAR.value):
                return True

            return False

        possibleQuips = list(filter(filterPredicate, self.quips))

        if (len(possibleQuips) == 0):
            return None

        return random.choice(possibleQuips) 

    def AddQuip(self, quip:str, type:int, user=None):
        newQuip = QuipData()
        newQuip.SetData(quip, type, user)
        self.quips.append(newQuip)

    def RemoveQuip(self, index:int):
        self.quips[index].delete() # remove entry from database
        self.quips.pop(index)
        
    def SetCurrentMapPool(self, poolName:str):
        self.currentPool = self.GetMapPoolProperName(poolName)
        self._currentPool = self.currentPool
        self.save()
