from mongoengine import Document, IntField, StringField
import discord

class PlayerData(Document):
    # Database fields.  Dont modify or access directly, use the non underscore versions
    _mmr = IntField(default=0)
    _matchesPlayed = IntField(default=0)
    _wins = IntField(default=0)
    _loses = IntField(default=0)
    _name = StringField(default='')
    _user = IntField(default=-1)

    # Settings
    mmr = 0
    matchesPlayed = 0
    wins = 0
    loses = 0
    name = '' # The name choosen by the user when registering
    user = None # discord.User

    def Init(self, bot):
        mmr = _mmr
        matchesPlayed = _matchesPlayed
        wins = _wins
        loses = _loses
        name = _name
        user = bot.get_user(_user)

    def SetUser(self, user:discord.User, name:str):
        self.user = user
        self._user = user.id
        self.name = name
        self._name = name
        self.save()

