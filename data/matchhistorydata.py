from enum import Enum

class MatchResult(Enum):
    TEAM1VICTORY = 0
    TEAM2VICTORY = 1
    CANCELLED = 2

class MatchHistoryData(object):
    def __init__(self):
        self.team1 = [] # Array<PlayerData>
        self.team2 = [] # Array<PlayerData>
        self.result = None # MatchResult
        self.map = ""
        self.creationTime = None # datetime.datetime
        self.matchNumber = 0
