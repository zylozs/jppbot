import discord
from data.botsettings import BotSettings, ChannelType, ChannelTypeInvalid, GuildTextChannelMismatch, GuildRoleMismatch, RegisteredRoleUnitialized, AdminRoleUnitialized
from data.mmrrole import InvalidMMRRole, MMRRoleExists, MMRRoleRangeConflict
from discord.ext import commands
from mongoengine import connect, disconnect

# Connect to our MongoDB
connect(db="jppbot")

# Load (or create) our settings
if (len(BotSettings.objects) > 0):
    botSettings = BotSettings.objects.first()
else:
    botSettings = BotSettings()

bot = commands.Bot(command_prefix='!', description='A bot to host the weekly JPP sessions.')

async def SendMessage(ctx, **kwargs):
    messageEmbed = discord.Embed(**kwargs)

    await ctx.send(embed=messageEmbed)

async def SendMessageWithFields(ctx, fields, **kwargs):
    messageEmbed = discord.Embed(**kwargs)

    for field in fields: 
        messageEmbed.add_field(name=field['name'], value=field['value'], inline=field['inline'])

    await ctx.send(embed=messageEmbed)

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    await botSettings.InitSettings(bot)

@bot.command(name='quit')
@commands.has_permissions(administrator=True)
async def OnQuit(ctx):
    disconnect() # disconect our MongoDB instance
    await bot.close() # close our bot instance

@bot.command(name='jpp')
async def OnJPP(ctx):
    await ctx.send(':jpp:')

@bot.command(name='register', aliases=['r'])
async def OnRegisterPlayer(ctx, name:str):
    print('User {0.author} is registering with name {1}'.format(ctx, name))

    if (botSettings.registeredRole is None):
        raise RegisteredRoleUnitialized()

    if (botSettings.IsUserRegistered(ctx.author)):
        await SendMessage(ctx, description='You are already registered!', color=discord.Color.blue())
        return

    try:
        await ctx.author.add_roles(botSettings.registeredRole, reason='User {0.name} used the register command'.format(ctx.author))

        botSettings.RegisterUser(ctx.author, name)

        await SendMessage(ctx, description='You have been registered as `{}`!'.format(name), color=discord.Color.blue())
    except discord.HTTPException:
        await SendMessage(ctx, description='Registration failed. Please try again.', color=discord.Color.red())

@bot.command(name='registeradmin')
@commands.has_permissions(administrator=True)
async def OnRegisterAdmin(ctx, member:discord.Member):
    print('User {0.author} is registering a new admin {1}'.format(ctx, member))

    if (botSettings.adminRole is None):
        raise AdminRoleUnitialized()

    try:
        await member.add_roles(botSettings.adminRole, reason='User {0.author} is registering a new admin {1}'.format(ctx, member))
        await SendMessage(ctx, description='You have registered {0.mention} as an admin!'.format(member), color=discord.Color.blue())
    except discord.HTTPException:
        await SendMessage(ctx, description='Registration failed. Please try again.', color=discord.Color.red())

@bot.command(name='removeadmin')
@commands.has_permissions(administrator=True)
async def OnRemoveAdmin(ctx, member:discord.Member):
    print('User {0.author} is removing admin permissions from {1}'.format(ctx, member))

    if (botSettings.adminRole is None):
        raise AdminRoleUnitialized()

    try:
        await member.remove_roles(botSettings.adminRole, reason='User {0.author} is removing admin permissions from {1}'.format(ctx, member))
        await SendMessage(ctx, description='You have removed admin permissions from {0.mention}.'.format(member), color=discord.Color.blue())
    except discord.HTTPException:
        await SendMessage(ctx, description='Removal failed. Please try again.', color=discord.Color.red())

@bot.command(name='join', aliases=['j'])
async def OnJoinQueue(ctx):
    #stub
    print('User {0.author} is joining'.format(ctx))

@bot.command(name='clearchannel')
@commands.has_permissions(administrator=True)
async def OnClearChannel(ctx, channel:discord.TextChannel, channelType:ChannelType):
    print('Channel: {} type: {}'.format(channel, channelType))

    if (channelType is ChannelType.LOBBY):
        botSettings.SetLobbyChannel(None)
    elif (channelType is ChannelType.REGISTER):
        botSettings.SetRegisterChannel(None)
    elif (channelType is ChannelType.ADMIN):
        botSettings.SetAdminChannel(None)
    elif (channelType is ChannelType.RESULTS):
        botSettings.SetResultsChannel(None)

    await SendMessage(ctx, description='{0.mention} has been cleared as the {1.value} channel'.format(channel, channelType), color=discord.Color.blue())

@bot.command(name='setchannel')
@commands.has_permissions(administrator=True)
async def OnSetChannel(ctx, channel:discord.TextChannel, channelType:ChannelType):
    print('Setting Channel: {} type: {}'.format(channel, channelType))

    # setup guild if missing
    if (botSettings.guild is None):
        botSettings.SetGuild(channel.guild)
    elif (botSettings.guild is not channel.guild):
        raise GuildTextChannelMismatch(channel)

    if (channelType is ChannelType.LOBBY):
        botSettings.SetLobbyChannel(channel)
    elif (channelType is ChannelType.REGISTER):
        botSettings.SetRegisterChannel(channel)
    elif (channelType is ChannelType.ADMIN):
        botSettings.SetAdminChannel(channel)
    elif (channelType is ChannelType.RESULTS):
        botSettings.SetResultsChannel(channel)

    await SendMessage(ctx, description='{0.mention} has been set as the {1.value} channel'.format(channel, channelType), color=discord.Color.blue())

@bot.command(name='setregisteredrole')
@commands.has_permissions(administrator=True)
async def OnSetRegisteredRole(ctx, role:discord.Role):
    print('Setting Registered Role: {}'.format(role))

    # setup guild if missing
    if (botSettings.guild is None):
        botSettings.SetGuild(role.guild)
    elif (botSettings.guild is not role.guild):
        raise GuildRoleMismatch(role)

    if (botSettings.registeredRole is not None):
        title = 'Warning: You are changing the registered role.'
        description = 'This will not affect players who are already registered. The previous role {0.mention} will not be automatically changed on registered players, however the role is purely cosmetic.'.format(botSettings.registeredRole)
        await SendMessage(ctx, title=title, description=description, color=discord.Color.gold())

    botSettings.SetRegisteredRole(role)
    await SendMessage(ctx, description='The registered role has been updated.', color=discord.Color.blue())

@bot.command(name='setadminrole')
@commands.has_permissions(administrator=True)
async def OnSetAdminRole(ctx, role:discord.Role):
    print('Setting Admin Role: {}'.format(role))

    # setup guild if missing
    if (botSettings.guild is None):
        botSettings.SetGuild(role.guild)
    elif (botSettings.guild is not role.guild):
        raise GuildRoleMismatch(role)

    if (botSettings.adminRole is not None):
        title = 'Warning: You are changing the admin role.'
        description = 'This may impact members with the previous admin role {0.mention}. They will need their role updated to regain admin priviledges with the bot.'.format(botSettings.adminRole)
        await SendMessage(ctx, title=title, description=description, color=discord.Color.gold())

    botSettings.SetAdminRole(role)
    await SendMessage(ctx, description='The admin role has been updated.', color=discord.Color.blue())

@bot.command(name='addrank')
@commands.has_permissions(administrator=True)
async def OnAddRank(ctx, role:discord.Role, mmrMin:int, mmrMax:int, mmrDelta:int):
    print('Adding new rank: {} min: {} max: {} delta: {}'.format(role, mmrMin, mmrMax, mmrDelta))

    # setup guild if missing
    if (botSettings.guild is None):
        botSettings.SetGuild(role.guild)
    elif (botSettings.guild is not role.guild):
        raise GuildRoleMismatch(role)

    if (botSettings.IsValidMMRRole(role)):
        raise MMRRoleExists(role)

    if (not botSettings.IsMMRRoleRangeValid(mmrMin, mmrMax)):
        raise MMRRoleRangeConflict()

    botSettings.AddMMRRole(role, mmrMin, mmrMax, mmrDelta)
    await SendMessage(ctx, title='New Rank Added', description='Role: {0.mention}\nMMR Range: {1}-{2}\nMMR Delta: +-{3}'.format(role, mmrMin, mmrMax, mmrDelta), color=discord.Color.blue())

@bot.command(name='updaterank')
@commands.has_permissions(administrator=True)
async def OnUpdateRank(ctx, role:discord.Role, mmrMin:int, mmrMax:int, mmrDelta:int):
    print('Updating existing rank: {} min: {} max: {} delta: {}'.format(role, mmrMin, mmrMax, mmrDelta))

    # setup guild if missing
    if (botSettings.guild is None):
        botSettings.SetGuild(role.guild)
    elif (botSettings.guild is not role.guild):
        raise GuildRoleMismatch(role)

    if (not botSettings.IsValidMMRRole(role)):
        raise InvalidMMRRole(role)

    if (not botSettings.IsMMRRoleRangeValid(mmrMin, mmrMax)):
        raise MMRRoleRangeConflict()

    botSettings.UpdateMMRRole(role, mmrMin, mmrMax, mmrDelta)
    await SendMessage(ctx, title='Rank Updated', description='Role: {0.mention}\nMMR Range: {1}-{2}\nMMR Delta: +-{3}'.format(role, mmrMin, mmrMax, mmrDelta), color=discord.Color.blue())

@bot.command(name='removerank')
@commands.has_permissions(administrator=True)
async def OnRemoveRank(ctx, role:discord.Role):
    print('Removing rank: {}'.format(role))

    # setup guild if missing
    if (botSettings.guild is None):
        botSettings.SetGuild(role.guild)
    elif (botSettings.guild is not role.guild):
        raise GuildRoleMismatch(role)

    if (not botSettings.IsValidMMRRole(role)):
        raise InvalidMMRRole(role)

    mmrMin = botSettings.mmrRoles[role.id].mmrMin
    mmrMax = botSettings.mmrRoles[role.id].mmrMax
    mmrDelta = botSettings.mmrRoles[role.id].mmrDelta

    botSettings.RemoveMMRRole(role)
    await SendMessage(ctx, title='Rank Removed', description='Role: {0.mention}\nMMR Range: {1}-{2}\nMMR Delta: +-{3}'.format(role, mmrMin, mmrMax, mmrDelta), color=discord.Color.blue())

@bot.command(name='ranks')
async def OnShowRanks(ctx):
    print('Showing ranks')

    description = None
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
        await SendMessageWithFields(ctx, fields=fields, color=discord.Color.blue())

@OnSetChannel.error
@OnClearChannel.error
@OnRegisterPlayer.error
@OnSetRegisteredRole.error
@OnRegisterAdmin.error
@OnRemoveAdmin.error
@OnSetAdminRole.error
@OnJoinQueue.error
@OnRegisterPlayer.error
@OnAddRank.error
@OnUpdateRank.error
@OnRemoveRank.error
@OnShowRanks.error
async def errorHandling(ctx, error):
    print('Error: {}'.format(error))
    if (isinstance(error, commands.ChannelNotFound)):
        await SendMessage(ctx, description='`{}` is not a valid text channel.'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, commands.RoleNotFound)):
        await SendMessage(ctx, description='`{}` is not a valid role.'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, ChannelTypeInvalid)):
        await SendMessage(ctx, description='`{}` is not a valid channel type.'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, RegisteredRoleUnitialized)):
        await SendMessage(ctx, description='The registered role has not been setup yet.', color=discord.Color.red())

    elif (isinstance(error, AdminRoleUnitialized)):
        await SendMessage(ctx, description='The admin role has not been setup yet.', color=discord.Color.red())

    elif (isinstance(error, GuildTextChannelMismatch)):
        await SendMessage(ctx, description='`{0.mention}` is not in the same server as the other text channels'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, GuildRoleMismatch)):
        await SendMessage(ctx, description='`{0.mention}` is not in the same server as the text channels'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, InvalidMMRRole)):
        await SendMessage(ctx, description='{0.mention} is not a valid rank.'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, MMRRoleExists)):
        await SendMessage(ctx, description='{0.mention} is already a rank.'.format(error.argument), color=discord.Color.red())

    elif (isinstance(error, MMRRoleRangeConflict)):
        await SendMessage(ctx, description='The MMR Range you provided overlaps with another rank.', color=discord.Color.red())

    elif (isinstance(error, commands.errors.MissingRequiredArgument)):
        await SendMessage(ctx, description='Invalid usage: `{0.name}` is a required argument'.format(error.param), color=discord.Color.red())

    elif (isinstance(error, commands.BadArgument)):
        await SendMessage(ctx, description='Bad Argument: {}'.format(error), color=discord.Color.red())

