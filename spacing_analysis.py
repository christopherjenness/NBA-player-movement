import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scrape import Game
import pandas as pd
import pickle

def extract_games():
    """
    Extract games from allgames.txt
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
           
def plot_spacing(date, home_team, away_team):
    filename = "{date}-{away_team}-{home_team}".format(date=date, away_team=away_team, home_team=home_team)
    plt.figure()
    plt.hist(f[1], bins=100, alpha=0.4, label=home_team)
    plt.hist(f[3], bins=100, alpha=0.4, label=away_team)
    plt.xlim(20,100)
    plt.legend(loc='upper right')
    plt.show()
    
plot_spacing('01.06.2016', 'OKC', 'MEM')

results = get_spacing_statistics('01.06.2016', 'OKC', 'MEM', write_file=True)
pickle.dump(results,  open( "testr.p", "wb"))
f = pickle.load(open( "data/spacing/01.06.2016-MEM-OKC", "rb" ))
home_offense_areas, home_defense_areas, away_offense_areas, away_defense_areas = [], [], [], []

for frame in range(len(test_game.moments)):
    offensive_team = test_game.get_offensive_team(frame)
    if offensive_team == 'home':
        home_offense_area, away_defense_area = test_game.get_spacing_area(frame)
        home_offense_areas.append(home_offense_area)
        away_defense_areas.append(away_defense_area)
    if offensive_team == 'away':
        home_defense_area, away_offense_area = test_game.get_spacing_area(frame)
        home_defense_areas.append(home_defense_area)
        away_offense_areas.append(away_offense_area)
    if frame % 1000 == 0:
        print(frame)
        

plt.figure()
plt.hist(f[1], bins=100, alpha=0.4, label='home')
plt.hist(f[3], bins=100, alpha=0.4, label='away')
plt.xlim(20,100)
plt.legend(loc='upper right')


np.mean(home_defense_areas)
np.mean(away_defense_areas)
