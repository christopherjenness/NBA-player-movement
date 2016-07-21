import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scrape import Game
import pandas as pd
import pickle

def extract_games():
    """
    Extract games from allgames.txt
    
    Returns:
        list: list of games.  Each element is list is [date, home_team, away_team]
        example element: ['01.01.2016', 'TOR', 'CHI']
    """
    games = []
    with open('allgames.txt', 'r') as f:
        for line in f:
            game = line.split('.')
            date = "{game[0]}.{game[1]}.{game[2]}".format(game=game)
            away = game[3]
            home = game[5]
            games.append([date, home, away])
    return games
    
def get_spacing_statistics(date, home_team, away_team, write_file=False):
    """
    Calculates spacing statistics for each frame in game
    
    Args:
        date (str): date of game in form 'MM.DD.YYYY'.  Example: '01.01.2016'
        home_team (str): home team in form 'XXX'. Example: 'TOR'
        away_team (str): away team in form 'XXX'. Example: 'CHI'
        write_file (bool): If True, write pickle file of statistics into data/spacing directory
        
    Returns: 
        tuple: tuple of data (home_offense_areas, home_defense_areas,
               away_offense_areas, away_defense_areas), where each element of the tuple
               is a list of convex hull areas for each frame in the game.
    """
    game = Game(date, home_team, away_team)
    home_offense_areas, home_defense_areas = [], []
    away_offense_areas, away_defense_areas = [], []

    for frame in range(len(game.moments)):
        offensive_team = game.get_offensive_team(frame)
        if offensive_team == 'home':
            home_offense_area, away_defense_area = game.get_spacing_area(frame)
            home_offense_areas.append(home_offense_area)
            away_defense_areas.append(away_defense_area)
        if offensive_team == 'away':
            home_defense_area, away_offense_area = game.get_spacing_area(frame)
            home_defense_areas.append(home_defense_area)
            away_offense_areas.append(away_offense_area)
        if frame % 1000 == 0:
            print(str(frame) + " / " + str(len(game.moments)))
    results = (home_offense_areas, home_defense_areas,
               away_offense_areas, away_defense_areas)

    if write_file:
        filename = "{date}-{away_team}-{home_team}".format(date=date, away_team=away_team, home_team=home_team)
        pickle.dump(results,  open( 'data/spacing/' + filename + '.p', "wb"))

    return(home_offense_areas, home_defense_areas,
           away_offense_areas, away_defense_areas)
           
def plot_spacing(date, home_team, away_team, defense=True):
    """
    Plots team's spacing distrubution in a game.
    
    Args:
        date (str): date of game in form 'MM.DD.YYYY'.  Example: '01.01.2016'
        home_team (str): home team in form 'XXX'. Example: 'TOR'
        away_team (str): away team in form 'XXX'. Example: 'CHI'
        defense (bool): if True, plot defensive spacing.  if False, plot offensive spacing
        
    Returns: None
        Also, shows plt.hist of team spacing during game
        
    """
    filename = "{date}-{away_team}-{home_team}".format(date=date, away_team=away_team, home_team=home_team)
    plt.figure()
    if defense:
        plt.hist(f[1], bins=100, alpha=0.4, label=home_team)
        plt.hist(f[3], bins=100, alpha=0.4, label=away_team)
    else:
        plt.hist(f[0], bins=100, alpha=0.4, label=home_team)
        plt.hist(f[1], bins=100, alpha=0.4, label=away_team)
    plt.xlim(20,100)
    plt.legend(loc='upper right')
    plt.show()
    
def write_spacing(gamelist):
    """
    Writes all spacing statistics to data/spacing directory for every game
    """
    for game in gamelist:
        get_spacing_statistics(game[0], game[1], game[2], write_file=True)

if __name__ == "__main__":
    games = extract_games()
    write_spacing(games)
