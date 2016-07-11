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
    
    def __init__(self, date, home_team, away_team, game_id):
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
        self.game_id = game_id
        self.tracking_id = date + '.' + away_team + '.at.' + home_team 
        self.pbp_data = None
        self._get_playbyplay_data()
        self.game_id = game_id
        self.tracking_data = None
        self._get_tracking_data()
        print('done')
    
    def _get_tracking_data(self):
        """
        Helper function for retrieving tracking data
        """
        link = "https://raw.githubusercontent.com/neilmj/BasketballData/master/2016.NBA.Raw.SportVU.Game.Logs/" + self.tracking_id + ".7z"
        #Extract Data into /data
        os.system("curl " + link + " -o " + os.getcwd() + "/data") 
        os.system("7za x " + os.getcwd() + "/data")
        
        with open('data/pbp_{gid}.json'.format(gid=self.game_id)) as data_file:
            self.tracking_data = json.load(data_file) # Load this json
        
        
    def _get_playbyplay_data(self):
        """
        Helper function for retrieving tracking data
        """
        os.system('curl "http://stats.nba.com/stats/playbyplayv2?'
            'EndPeriod=0&'
            'EndRange=0&'
            'GameID={gid}&'
            'RangeType=0&'
            'Season=2015-16&'
            'SeasonType=Season&'
            'StartPeriod=0&'
            'StartRange=0" > {cwd}/data/pbp_{gid}.json'.format(cwd=os.getcwd(), gid=self.game_id))
        with open("pbp_{gid}.json".format(gid=self.game_id)) as json_file:
            parsed = json.load(json_file)['resultSets'][0]
        self.pbp = pd.DataFrame(parsed['rowSet'])
        self.pbp.columns= parsed['headers']
        return self

# Using http://opiateforthemass.es/articles/animate-nba-shot-events/ for help
a = Game('01.13.2016', 'DEN', 'GSW', '0021500583')             
             
             
             
             
             
             
             
             
             
             
             