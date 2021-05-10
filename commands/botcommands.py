import discord
from data.botsettings import BotSettings, ChannelType, ChannelTypeInvalid
from discord.ext import commands

bot = commands.Bot(command_prefix='!', description='A bot to host the weekly JPP sessions.')
botSettings = BotSettings()

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

@bot.command()
@commands.has_permissions(administrator=True)
async def quit(ctx):
    await bot.close()

@bot.command()
async def jpp(ctx):
    await ctx.send(':jpp:')

@bot.command(aliases=['j'])
async def join(ctx):
    #stub
    print('User {0.author} is joining'.format(ctx))

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx, channel:discord.TextChannel, channelType:ChannelType):
    print('Channel: {} type: {}'.format(channel, channelType))

    if (channelType is ChannelType.LOBBY):
        botSettings.lobbyChannel = channel
    elif (channelType is ChannelType.REGISTER):
        botSettings.registerChannel = channel
    elif (channelType is ChannelType.REPORT):
        botSettings.reportChannel = channel
    elif (channelType is ChannelType.RESULTS):
        botSettings.resultsChannel = channel

    await ctx.send('{0.mention} has been set as the {1.value} channel'.format(channel, channelType))

@setup.error
async def setup_error(ctx, error):
    print('Error: {}'.format(error))
    if (isinstance(error, commands.ChannelNotFound)):
        await ctx.send('`{}` is not a valid text channel.'.format(error.argument))

    if (isinstance(error, ChannelTypeInvalid)):
        await ctx.send('`{}` is not a valid channel type.'.format(error.argument))

