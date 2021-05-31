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
from commands.helpcommand import HelpCommand 
from discord.ext import commands
import discord

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
bot = commands.Bot(command_prefix='!', description='A bot to host the weekly JPP sessions.', intents=intents)
bot.add_cog(AdminCommands(bot))
bot.add_cog(BotCommands(bot))
bot.help_command = HelpCommand()

matchService.Init(bot, botSettings)

bot.run(token)
