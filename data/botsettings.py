from data.playerdata import PlayerData
from data.mmrrole import MMRRole 
from data.matchhistorydata import MatchHistoryData
from services.matchservice import TeamResult
from data.siegemap import SiegeMap
from enum import Enum
from discord.ext import commands
from mongoengine import Document, IntField 
import discord
import random
import math

class ChannelTypeInvalid(commands.BadArgument):
	def __init__(self, argument):
		self.argument = argument
		super().__init__('Channel Type "{}" is not valid.'.format(argument))

class RegisteredRoleUnitialized(commands.CommandError):
	def __init__(self):
		super().__init__('The registered role has not been setup.')

class AdminRoleUnitialized(commands.CommandError):
	def __init__(self):
		super().__init__('The admin role has not been setup.')

class UserNotAdmin(commands.CommandError):
	def __init__(self, argument):
		self.argument = argument
		super().__init__('The user {0.mention} is not an admin'.format(argument))

class GuildTextChannelMismatch(commands.BadArgument):
	def __init__(self, argument):
		self.argument = argument
		super().__init__('Text Channel "{0.mention}" is not in the same guild as the other text channels.'.format(argument))

class GuildRoleMismatch(commands.BadArgument):
	def __init__(self, argument):
		self.argument = argument
		super().__init__('Role {0.mention}" is not in the same guild as the text channels.'.format(argument))

class InvalidGuild(commands.BadArgument):
	def __init__(self):
		super().__init__('There is no guild set.')

class InvalidCommandChannel(commands.BadArgument):
	def __init__(self, argument, type):
		self.argument = argument
		self.type = type
		super().__init__('{0.mention} is not the correct channel for {1.value} commands'.format(argument, type))

class EmptyName(commands.BadArgument):
	def __init__(self):
		super().__init__('An empty string is not a valid name.')

class ChannelType(Enum):
	LOBBY = "lobby"
	RESULTS = "result"
	ADMIN = "admin"
	REGISTER = "register"
	REPORT = "report"
	INVALID = "invalid"

	@classmethod
	async def convert(cls, ctx, argument):
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
			self.registeredPlayers[player.user.id] = player

		self.registeredRole = self._GetRole(self._registeredRole)
		self.adminRole = self._GetRole(self._adminRole)

		# MMR Rank definition
		# Type: Dictionary<key=discord.Role, value=MMRRole>
		self.mmrRoles = {}

		for role in MMRRole.objects:
			role.Init(self.guild)
			self.mmrRoles[role.role.id] = role 

		# Maps
		self.maps = {}

		for _map in SiegeMap.objects:
			_map.Init()
			self.maps[_map.name.lower()] = _map

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
		self.maps[name.lower()].delete() # remove entry from database
		del self.maps[name.lower()]

	def SetMapThumbnail(self, name:str, thumbnailURL:str):
		self.maps[name.lower()].SetThumbnail(thumbnailURL)

	def GetMapThumbnail(self, name:str):
		return self.maps[name.lower()].thumbnailURL

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

	def GetUserName(self, user:discord.User):
		return self.GetUserNameByID(user.id)

	def GetUserNameByID(self, id:int):
		return self.registeredPlayers[id].name

	def IsUserRegistered(self, user:discord.User):
		return self.IsUserRegisteredByID(user.id)

	def IsUserRegisteredByID(self, id:int):
		return id in self.registeredPlayers

	def IsUserAdmin(self, user:discord.Member):
		return self.adminRole in user.roles

	def IsValidMMRRole(self, role:discord.Role):
		return role.id in self.mmrRoles

	def DoesMapExist(self, name:str):
		return name.lower() in self.maps

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

	def GetRandomMap(self, enablePMCCOverride = False):
		# sort by times played. Less played maps towards the beginning and more played maps towards the end
		sortedMaps = sorted(self.maps.values(), key=lambda _map : _map.timesPlayed)

		# random amongst the least played maps (numMaps / 3)
		numMapsToKeep = int(math.ceil(len(sortedMaps) / 3))

		leastPlayedMaps = sortedMaps[:numMapsToKeep]

		if ('villa' in self.maps and enablePMCCOverride):
			if (self.maps['villa'] not in leastPlayedMaps):
				leastPlayedMaps.append(self.maps['villa'])

		return random.choice(leastPlayedMaps)

	def DeclareMapPlayed(self, mapName:str):
		self.maps[mapName.lower()].IncrementTimesPlayed()

	def DeclareWinner(self, user:discord.User, mmrDelta=None):
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

		return oldMMR, newMMR, oldRole, newRole

	def DeclareLoser(self, user:discord.User, mmrDelta=None):
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

		return oldMMR, newMMR, oldRole, newRole

	def DeclareCancel(self, user:discord.User):
		return self.DeclareCancelByID(user.id)

	def DeclareCancelByID(self, id:int):
		oldRole, newRole= self.GetMMRRoleByID(id)

		oldMMR = self.GetMMRByID(id)
		newMMR = oldMMR

		mmrDelta = 0
		if (newRole is not None):
			mmrDelta = newRole.mmrDelta

		return oldMMR, newMMR, mmrDelta

	def RedoMatch(self, user:discord.User, mmrDelta:int, prevResult:TeamResult, newResult:TeamResult):
		return self.RedoMatchByID(user.id, mmrDelta, prevResult, newResult)

	def RedoMatchByID(self, id:int, mmrDelta:int, prevResult:TeamResult, newResult:TeamResult):
		oldMMR = self.GetMMRByID(id)

		self.registeredPlayers[id].RedoData(mmrDelta, prevResult, newResult)

		newMMR = self.GetMMRByID(id)
		oldRole, newRole = self.GetMMRRoleByID(id, oldMMR)

		# Return none if we aren't changing roles
		if (oldRole is not None and oldRole is newRole):
			oldRole = None
			newRole = None

		return oldMMR, newMMR, oldRole, newRole


