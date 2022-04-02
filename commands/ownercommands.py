from discord.ext import commands
from data.botsettings import EmptyName, InvalidGuild, InvalidActivityIndex
from data.activitydata import ActivityType, InvalidActivityType
from utils.chatutils import SendMessage
from utils.botutils import IsPrivateMessage, IsOwner 
from utils.errorutils import HandleError
from globals import *
import discord

class OwnerCommands(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(name='setnickname')
	@IsPrivateMessage()
	@IsOwner()
	async def OnSetNickname(self, ctx, *name):
		"""Allows the owner to change the nickname of the bot"""
		if (len(name) == 0):
			raise EmptyName()

		if (botSettings.guild is None):
			raise InvalidGuild()

		combinedName = ' '.join(name)
		member = botSettings.guild.get_member(self.bot.user.id)
		await member.edit(nick=combinedName)
		await SendMessage(ctx, description='Changing nickname to `{}`'.format(combinedName), color=discord.Color.blue())

	@commands.command(name='addactivity')
	@IsPrivateMessage()
	@IsOwner()
	async def OnAddActivity(self, ctx, type:ActivityType, *name):
		"""Adds an activity for the bot to do
		
		   **string|int:** <type>
		   The type of activity you want to have.
		   Available results (not case sensitive):
		   - 0 (Game)
		   - 1 (Watching)
		   - 2 (Listening)
		   - game (Game)
		   - g (Game)
		   - watch (Watching)
		   - w (Watching)
		   - listen (Listening)
		   - l (Listening)

		   **string:** <name>
		   The name you want to show for the activity.
		"""
		if (type == ActivityType.INVALID):
			raise InvalidActivityType(type)

		if (len(name) == 0):
			raise EmptyName()

		combinedName = ' '.join(name)
		botSettings.AddActivity(combinedName, type.value)

		await SendMessage(ctx, description='Activity `{}` added'.format(combinedName), color=discord.Color.blue())

	@commands.command(name='showactivities')
	@IsPrivateMessage()
	@IsOwner()
	async def OnShowActivities(self, ctx):
		"""Shows the activities the bot can choose from"""
		if (len(botSettings.activities) == 0):
			await SendMessage(ctx, description='There are no activities yet!', color=discord.Color.blue())
			return

		message = ''
		index = 0
		for activity in botSettings.activities:
			type = await ActivityType.convert(ctx, activity.type)
			message += '{}. [{}] `{}`\n'.format(index, type.name, activity.name)
			index += 1

		await SendMessage(ctx, description=message, color=discord.Color.blue())

	@commands.command(name='removeactivity')
	@IsPrivateMessage()
	@IsOwner()
	async def OnRemoveActivity(self, ctx, index:int):
		"""Removes an activity that the bot can do 
		   
		   **int:** <index>
		   The index of the activity you want to remove.
		"""
		if (len(botSettings.activities) == 0):
			await SendMessage(ctx, description='There are no activities yet!', color=discord.Color.blue())
			return

		if (index < 0 or index >= len(botSettings.activities)):
			raise InvalidActivityIndex(index)

		activityName = botSettings.activities[index].name
		botSettings.RemoveActivity(index)

		await SendMessage(ctx, description='Activity `{}` removed'.format(activityName), color=discord.Color.blue())

	@OnSetNickname.error
	@OnAddActivity.error
	@OnShowActivities.error
	@OnRemoveActivity.error
	async def errorHandling(self, ctx, error):
		await HandleError(ctx, error)

