from data.playerdata import PlayerData
from data.mmrrole import MMRRole 
from data.matchhistorydata import MatchHistoryData
from data.siegemap import SiegeMap
from enum import Enum
from discord.ext import commands
from mongoengine import Document, IntField 
import discord
import random

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

class ChannelType(Enum):
	LOBBY = "lobby"
	RESULTS = "result"
	ADMIN = "admin"
	REGISTER = "register"
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
	_registeredRole = IntField(default=-1)
	_adminRole = IntField(default=-1)
	_nextUniqueMatchID = IntField(default=0)

	# Settings
	guild = None # discord.Guild
	lobbyChannel = None # discord.TextChannel
	resultsChannel = None # discord.TextChannel
	adminChannel = None # discord.TextChannel
	registerChannel = None # discord.TextChannel
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

	def AddMMRRole(self, role:discord.Role, mmrMin:int, mmrMax:int, mmrDelta:int):
		newRole = MMRRole()
		newRole.SetData(role, mmrMin, mmrMax, mmrDelta)
		self.mmrRoles[role.id] = newRole 

	def UpdateMMRRole(self, role:discord.Role, mmrMin:int, mmrMax:int, mmrDelta:int):
		self.mmrRoles[role.id].UpdateData(mmrMin, mmrMax, mmrDelta)

	def RemoveMMRRole(self, role:discord.Role):
		self.mmrRoles[role.id].delete() # remove entry from database
		del self.mmrRoles[role.id]

	def AddMap(self, name:str):
		_map = SiegeMap()
		_map.SetName(name)
		self.maps[name.lower()] = _map
	
	def RemoveMap(self, name:str):
		self.maps[name.lower()].delete() # remove entry from database
		del self.maps[name.lower()]

	def SetMMR(self, user:discord.User, mmr:int):
		previousMMR = self.registeredPlayers[user.id].mmr
		self.registeredPlayers[user.id].SetMMR(mmr)
		return previousMMR

	def GetMMR(self, user:discord.User):
		return self.registeredPlayers[user.id].mmr

	def GetMMRRole(self, user:discord.User, previousMMR:int = -1):
		mmr = self.registeredPlayers[user.id].mmr
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

	def GetSortedMMRRoles(self):
		return sorted(self.mmrRoles.values(), key=lambda role: role.mmrMin)

	def GetSortedMaps(self):
		return sorted(self.maps.values(), key=lambda _map : _map.name.lower())

	def GetUserName(self, user:discord.User):
		return self.registeredPlayers[user.id].name

	def IsUserRegistered(self, user:discord.User):
		return user.id in self.registeredPlayers

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

		if (returnType is False and channel is self.adminChannel and includeAdmin):
			returnType = True

		return returnType 

	def GetNextUniqueMatchID(self):
		id = self._nextUniqueMatchID
		self._nextUniqueMatchID += 1
		self.save()
		return id

	def GetRandomMap(self):
		return random.choice(self.GetSortedMaps())

	def DeclareMapPlayed(self, mapName:str):
		self.maps[mapName.lower()].IncrementTimesPlayed()

	def DeclareWinner(self, user:discord.User):
		oldRole, newRole= self.GetMMRRole(user)

		oldMMR = self.GetMMR(user)

		mmrDelta = 0
		if (newRole is not None):
			mmrDelta = newRole.mmrDelta

		self.registeredPlayers[user.id].UpdateData(mmrDelta, True)

		newMMR = self.GetMMR(user)
		oldRole, newRole = self.GetMMRRole(user, oldMMR)

		# Return none if we aren't changing roles
		if (oldRole is not None and oldRole is newRole):
			oldRole = None
			newRole = None

		return oldMMR, newMMR, oldRole, newRole


	def DeclareLoser(self, user:discord.User):
		oldRole, newRole= self.GetMMRRole(user)

		oldMMR = self.GetMMR(user)

		mmrDelta = 0
		if (newRole is not None):
			mmrDelta = newRole.mmrDelta

		self.registeredPlayers[user.id].UpdateData(mmrDelta, False)

		newMMR = self.GetMMR(user)
		oldRole, newRole = self.GetMMRRole(user, oldMMR)

		# Return none if we aren't changing roles
		if (oldRole is not None and oldRole is newRole):
			oldRole = None
			newRole = None

		return oldMMR, newMMR, oldRole, newRole

