import discord
from data.botsettings import BotSettings, ChannelType, ChannelTypeInvalid, GuildTextChannelMismatch
from discord.ext import commands
from mongoengine import connect, disconnect

# Connect to our MongoDB
connect(db="jppbot")

# Load (or create) our settings
if (len(BotSettings.objects) > 0):
    botSettings = BotSettings.objects[0]
else:
    botSettings = BotSettings()

bot = commands.Bot(command_prefix='!', description='A bot to host the weekly JPP sessions.')

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    botSettings.InitSettings(bot)

@bot.command()
@commands.has_permissions(administrator=True)
async def quit(ctx):
    disconnect() # disconect our MongoDB instance
    await bot.close() # close our bot instance

@bot.command()
async def jpp(ctx):
    await ctx.send(':jpp:')

@bot.command(aliases=['r'])
async def register(ctx, name:str):
    #stub
    print('User {0.author} is registering with name {1}'.format(ctx, name))

@bot.command(aliases=['j'])
async def join(ctx):
    #stub
    print('User {0.author} is joining'.format(ctx))

@bot.command()
@commands.has_permissions(administrator=True)
async def clearchannel(ctx, channel:discord.TextChannel, channelType:ChannelType):
    print('Channel: {} type: {}'.format(channel, channelType))

    if (channelType is ChannelType.LOBBY):
        botSettings.SetLobbyChannel(None)
    elif (channelType is ChannelType.REGISTER):
        botSettings.SetRegisterChannel(None)
    elif (channelType is ChannelType.REPORT):
        botSettings.SetReportChannel(None)
    elif (channelType is ChannelType.RESULTS):
        botSettings.SetResultsChannel(None)

    await ctx.send('{0.mention} has been cleared as the {1.value} channel'.format(channel, channelType))

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx, channel:discord.TextChannel, channelType:ChannelType):
    print('Channel: {} type: {}'.format(channel, channelType))

    # setup guild if missing
    if (botSettings.guild is None):
        botSettings.SetGuild(channel.guild)
    elif (botSettings.guild is not channel.guild):
        raise GuildTextChannelMismatch(channel)
        return

    if (channelType is ChannelType.LOBBY):
        botSettings.SetLobbyChannel(channel)
    elif (channelType is ChannelType.REGISTER):
        botSettings.SetRegisterChannel(channel)
    elif (channelType is ChannelType.REPORT):
        botSettings.SetReportChannel(channel)
    elif (channelType is ChannelType.RESULTS):
        botSettings.SetResultsChannel(channel)

    await ctx.send('{0.mention} has been set as the {1.value} channel'.format(channel, channelType))

@setup.error
@clearchannel.error
@register.error
async def errorHandling(ctx, error):
    print('Error: {}'.format(error))
    if (isinstance(error, commands.ChannelNotFound)):
        await ctx.send('`{}` is not a valid text channel.'.format(error.argument))

    if (isinstance(error, ChannelTypeInvalid)):
        await ctx.send('`{}` is not a valid channel type.'.format(error.argument))

    if (isinstance(error, GuildTextChannelMismatch)):
        await ctx.send('`{0.mention}` is not in the same server as the other text channels'.format(error.argument))

    if (isinstance(error, commands.errors.MissingRequiredArgument)):
        await ctx.send('Invalid usage: `{0.name}` is a required argument'.format(error.param))

