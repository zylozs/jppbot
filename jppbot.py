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

        # If you need to specifically test global commands within a guild only context, uncomment this
        #guild = discord.Object(botSettings._guild)
        # We'll copy in the global commands to test with:
        #self.tree.copy_global_to(guild=guild)
        # followed by syncing to the testing guild.
        #await self.tree.sync(guild=guild)

        # sync the global commands
        await self.tree.sync()

    # Override the default error handling to try and handle non-command errors
    async def on_command_error(self, ctx, error):
        command = ctx.command
        if command and command.has_error_handler():
            return

        await HandleError(ctx, error)

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.guilds = True
intents.message_content = True
bot = JPPBot(command_prefix='!', description='A bot to host the weekly JPP sessions.\nFor Slash Command help, just start typing / and see what JPP Bot provides!', intents=intents)

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
stratRouletteService.Init(bot, botSettings)

bot.run(token)
