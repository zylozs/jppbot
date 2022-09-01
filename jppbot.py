from mongoengine import connect
import sys
import getopt

# Get our commandline args if any
try:
    cmdOptions, cmdArgs = getopt.getopt(sys.argv[1:], 'i:p:t:', ['ip=', 'port=', 'token='])
except getopt.GetoptError:
    print('Invalid arg usage')
    sys.exit(2)

ip = 'localhost'
port = '27017'
token = ''

for option, arg in cmdOptions:
    if (option in ('-i', '--ip')):
        ip = arg
    elif (option in ('-p', '--port')):
        port = arg
    elif (option in ('-t', '--token')):
        token = arg

# Connect to our MongoDB
print('Trying to connect to DB')
connect(db="jppbot", host=ip, port=int(port))

from globals import *
from commands.admincommands import AdminCommands
from commands.botcommands import BotCommands 
from commands.ownercommands import OwnerCommands 
from commands.helpcommand import HelpCommand 
from discord.ext import commands
import discord

class JPPBot(commands.Bot):
    async def setup_hook(self) -> None:
        await self.add_cog(AdminCommands(self))
        await self.add_cog(BotCommands(self))
        await self.add_cog(OwnerCommands(self))
        self.help_command = HelpCommand()
        

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.guilds = True
intents.message_content = True
bot = JPPBot(command_prefix='!', description='A bot to host the weekly JPP sessions.', intents=intents)

# We dont want people dming the bot to run commands
from utils.errorutils import HandleError, NoPrivateMessages

@bot.check
async def block_dms(ctx):
    if (botSettings.IsUserOwner(ctx.author)):
        return True 
    if (ctx.guild is None):
        raise NoPrivateMessages()
    return ctx.guild is not None

matchService.Init(bot, botSettings)

bot.run(token)
