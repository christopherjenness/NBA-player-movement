"""
Library for retrieving basektball player-tracking and play-by-play data.
"""

import os
import json
import pandas as pd

class Game(object):
    """
    Class for basketball game.
    """
    
    def __init__(self, date, home_team, away_team):
        """
        Args:
            date (str): 'MM.DD.YYYY', date of game
            home_team (str): 'XXX', abbreviation of home team
            away_team (str): 'XXX', abbreviation of home team
        
        Attributes:
            date (str): 'MM.DD.YYYY', date of game
            home_team (str): 'XXX', abbreviation of home team
            away_team (str): 'XXX', abbreviation of home team
            tracking_id (str): id to access player tracking data
                Due to the way the SportVU data is stored, game_id is 
                complicated: 'MM.DD.YYYY.AWAYTEAM.at.HOMETEAM'
                For Example: 01.13.2016.GSW.at.DEN
        """
        self.date = date
        self.home_team = home_team
        self.away_team = away_team
        self.tracking_id = date + '.' + away_team + '.at.' + home_team 