from data.botsettings import BotSettings
from services.matchservice import MatchService
from services.stratrouletteservice import StratRouletteService 

# Load (or create) our settings
if (len(BotSettings.objects) > 0):
    botSettings = BotSettings.objects.first()
else:
    botSettings = BotSettings()

matchService = MatchService()
stratRouletteService = StratRouletteService()
