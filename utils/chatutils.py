import discord

def CreateEmbed(**kwargs):
    messageEmbed = discord.Embed()

    if 'title' in kwargs:
        messageEmbed.title = kwargs['title']

    if 'type' in kwargs:
        messageEmbed.type = kwargs['type']

    if 'description' in kwargs:
        messageEmbed.description = kwargs['description']

    if 'url' in kwargs:
        messageEmbed.url = kwargs['url']

    if 'timestamp' in kwargs:
        messageEmbed.timestamp = kwargs['timestamp']

    if 'color' in kwargs:
        messageEmbed.color = kwargs['color']

    if 'fields' in kwargs:
        for field in kwargs['fields']: 
            if field['value'] == '':
                field['value'] = 'Empty'

            messageEmbed.add_field(name=field['name'], value=field['value'], inline=field['inline'])

    if 'footer' in kwargs:
        messageEmbed.set_footer(text=kwargs['footer'])

    if 'thumbnail' in kwargs:
        messageEmbed.set_thumbnail(url=kwargs['thumbnail'])

    return messageEmbed

async def SendMessage(interaction:discord.Interaction, ephemeral=False, **kwargs):
    await interaction.response.send_message(embed=CreateEmbed(**kwargs), ephemeral=ephemeral)

async def EditViewMessage(interaction:discord.Interaction, view=None, **kwargs):
    await interaction.response.edit_message(embed=CreateEmbed(**kwargs), view=view)

async def SendMessageEdit(interaction:discord.Interaction, **kwargs):
    await interaction.edit_original_response(embed=CreateEmbed(**kwargs))

async def SendMessages(interaction:discord.Interaction, messages, **kwargs):
    if (len(messages) >= 1):
        await interaction.response.send_message(embed=CreateEmbed(fields=messages[0], **kwargs))
        messages.pop(0)

    for message in messages:
        await SendChannelMessage(interaction.channel, fields=message, **kwargs)

async def SendChannelMessage(channel:discord.TextChannel, **kwargs):
    view = None

    if 'view' in kwargs:
        view = kwargs['view']

    message = await channel.send(embed=CreateEmbed(**kwargs), view=view)

    if 'reactions' in kwargs:
        for reaction in kwargs['reactions']:
            await message.add_reaction(reaction)

    return message
