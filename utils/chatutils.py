import discord

async def SendMessage(ctx, **kwargs):
    messageEmbed = discord.Embed(**kwargs)

    await ctx.send(embed=messageEmbed)

async def SendMessageWithFields(ctx, fields, **kwargs):
    messageEmbed = discord.Embed(**kwargs)

    for field in fields: 
        messageEmbed.add_field(name=field['name'], value=field['value'], inline=field['inline'])

    await ctx.send(embed=messageEmbed)

