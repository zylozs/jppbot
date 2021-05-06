import discord
from data.botsettings import BotSettings, ChannelType
from discord.ext import commands

description = 'A bot to host the weekly JPP sessions.'

bot = commands.Bot(command_prefix='!', description=description)
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
    print('Channel type: {}'.format(channelType))


# TODO: Extract token to a file and have the user create their own to run the bot
bot.run('ODM5MTc4OTcyMjAxODc3NTQ0.YJF4Ug.Tq8G4ZaWnegsdDQLov2w4YxR17o')
