import discord

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

# TODO: Extract token to a file and have the user create their own to run the bot
client.run('ODM5MTc4OTcyMjAxODc3NTQ0.YJF4Ug.Tq8G4ZaWnegsdDQLov2w4YxR17o')
