import discord

async def SendMessage(ctx, **kwargs):
   return await SendChannelMessage(ctx.channel, **kwargs)

async def SendMessages(ctx, messages, **kwargs):
    for message in messages:
        await SendChannelMessage(ctx.channel, fields=message, **kwargs)

async def SendChannelMessage(channel:discord.TextChannel, **kwargs):
    messageEmbed = discord.Embed(**kwargs)

    if 'fields' in kwargs:
        for field in kwargs['fields']: 
            if field['value'] == '':
                field['value'] = 'Empty'

            messageEmbed.add_field(name=field['name'], value=field['value'], inline=field['inline'])

    if 'footer' in kwargs:
        messageEmbed.set_footer(text=kwargs['footer'])

    if 'thumbnail' in kwargs:
        messageEmbed.set_thumbnail(url=kwargs['thumbnail'])

    message = await channel.send(embed=messageEmbed)

    if 'reactions' in kwargs:
        for reaction in kwargs['reactions']:
            await message.add_reaction(reaction)

    return message
