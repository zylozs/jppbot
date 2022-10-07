from discord.ext import commands
from data.botsettings import EmptyName, InvalidGuild, InvalidActivityIndex, InvalidQuipIndex, EmptyQuip
from data.activitydata import ActivityType, InvalidActivityType, NoActivities
from data.quipdata import NoQuips, QuipType, InvalidQuipType, InvalidGuildEmoji
from utils.chatutils import SendChannelMessage 
from utils.botutils import IsPrivateMessage, IsOwner 
from utils.errorutils import HandleError
from globals import *
import inspect
import discord
import emojis

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
        await SendChannelMessage(ctx.channel, description='Changing nickname to `{}`'.format(combinedName), color=discord.Color.blue())

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

        await SendChannelMessage(ctx.channel, description='Activity `{}` added'.format(combinedName), color=discord.Color.blue())

    @commands.command(name='activities')
    @IsPrivateMessage()
    @IsOwner()
    async def OnShowActivities(self, ctx):
        """Shows the activities the bot can choose from"""
        if (len(botSettings.activities) == 0):
            raise NoActivities()

        message = ''
        index = 0
        for activity in botSettings.activities:
            type = await ActivityType.convert(ctx, activity.type)
            message += '{}. [{}] `{}`\n'.format(index, type.name, activity.name)
            index += 1

        await SendChannelMessage(ctx.channel, description=message, color=discord.Color.blue())

    @commands.command(name='removeactivity')
    @IsPrivateMessage()
    @IsOwner()
    async def OnRemoveActivity(self, ctx, index:int):
        """Removes an activity that the bot can do 
           
           **int:** <index>
           The index of the activity you want to remove.
        """
        if (len(botSettings.activities) == 0):
            raise NoActivities()

        if (index < 0 or index >= len(botSettings.activities)):
            raise InvalidActivityIndex(index)

        activityName = botSettings.activities[index].name
        botSettings.RemoveActivity(index)

        await SendChannelMessage(ctx.channel, description='Activity `{}` removed'.format(activityName), color=discord.Color.blue())

    @commands.command(name='addquip')
    @IsPrivateMessage()
    @IsOwner()
    async def OnAddQuip(self, ctx, type:QuipType, *quip):
        """Adds a quip the bot can respond with when mentioned 

            **string|int:** <type>
           The type of quip you want to have.
           Available results (not case sensitive):
           - 0 (Regular)
           - 1 (Guild Emoji)
           - 2 (Specific User)
           - regular (Regular)
           - r (Regular)
           - emoji (Guild Emoji)
           - e (Guild Emoji)
           - user (Specific User)
           - u (Specific User)

           !! If Specific User Selected !!
           **discord.User:** <user>
           The discord user you want this quip to be specific to

           **string:** <quip>
           The quip you want to add.
        """
        if (type == QuipType.INVALID):
            raise InvalidQuipType(type)

        if (type == QuipType.SPECIFIC_USER and len(quip) == 0):
            raise commands.errors.MissingRequiredArgument(inspect.Parameter('user', inspect.Parameter.POSITIONAL_ONLY))

        if (type == QuipType.SPECIFIC_USER and len(quip) < 2):
            raise EmptyQuip()

        if (len(quip) == 0):
            raise EmptyQuip()

        if (botSettings.guild is None):
            raise InvalidGuild()

        combinedQuip = ' '.join(quip)
        combinedQuip = emojis.decode(combinedQuip)

        if (type == QuipType.GUILD_EMOJI and not discord.utils.get(botSettings.guild.emojis, name=combinedQuip)):
            raise InvalidGuildEmoji(combinedQuip)

        user = None
        additionalInfo = ' '
        if (type == QuipType.SPECIFIC_USER):
            converter = commands.UserConverter()
            user = await converter.convert(ctx, quip[0])
            additionalInfo = '[{}] '.format(user.mention)
            quip = quip[1:]
            combinedQuip = ' '.join(quip)

        botSettings.AddQuip(combinedQuip, type.value, user)

        message = '[{}]{}Quip added `{}`'.format(type.name, additionalInfo, combinedQuip)

        await SendChannelMessage(ctx.channel, description=message, color=discord.Color.blue())

    @commands.command(name='quips')
    @IsPrivateMessage()
    @IsOwner()
    async def OnShowQuips(self, ctx):
        """Shows the quips the bot can respond with"""
        if (len(botSettings.quips) == 0):
            raise NoQuips()

        fields = []
        heading = 'Quips'

        def CreateField():
            field = {}
            field['name'] = heading
            field['value'] = ''
            field['inline'] = False 

            return field

        field = CreateField() 

        message = ''
        index = 0
        for quip in botSettings.quips:
            type = await QuipType.convert(ctx, quip.type)
            additionalInfo = ' '

            if (type == QuipType.SPECIFIC_USER):
                additionalInfo = '[{}] '.format(quip.user.mention if quip.user else quip._user)

            newText = '{}. [{}]{}`{}`\n'.format(index, type.name, additionalInfo, quip.quip)
            
            # if the message is too long, we need to add a new field
            if (len(message) + len(newText) > 1024):
                field['value'] += message
                fields.append(field)
                field = CreateField()
                message = ''

            message += newText
            index += 1

        field['value'] += message
        fields.append(field)

        numPages = len(fields)
        if (numPages > 1):
            page = 0
            for field in fields:
                page += 1
                field['name'] = '{}{}'.format(heading, ' [{}/{}]'.format(page, numPages))

        await SendChannelMessage(ctx.channel, fields=fields, color=discord.Color.blue())

    @commands.command(name='removequip')
    @IsPrivateMessage()
    @IsOwner()
    async def OnRemoveQuip(self, ctx, index:int):
        """Removes a quip 
           
           **int:** <index>
           The index of the quip you want to remove.
        """
        if (len(botSettings.quips) == 0):
            raise NoQuips()

        if (index < 0 or index >= len(botSettings.quips)):
            raise InvalidQuipIndex(index)

        quip = botSettings.quips[index].quip
        type = await QuipType.convert(ctx, botSettings.quips[index].type)
        user = botSettings.quips[index].user
        botSettings.RemoveQuip(index)

        additionalInfo = ' '
        if (type == QuipType.SPECIFIC_USER and user):
            additionalInfo = '[{}] '.format(user.mention)

        message = '[{}]{}Quip removed `{}`'.format(type.name, additionalInfo, quip)

        await SendChannelMessage(ctx.channel, description=message, color=discord.Color.blue())

    @OnSetNickname.error
    @OnAddActivity.error
    @OnShowActivities.error
    @OnRemoveActivity.error
    @OnAddQuip.error
    @OnShowQuips.error
    @OnRemoveQuip.error
    async def errorHandling(self, ctx, error):
        await HandleError(ctx, error)

