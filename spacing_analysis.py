import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scrape import Game

#Extract games from allgames.txt
games = []
with open('allgames.txt', 'r') as f:
    for line in f:
        game = line.split('.')
        print(line, game)
        date = "{game[0]}.{game[1]}.{game[2]}".format(game=game)
        away = game[3]
        home = game[5]
        games.append([date, home, away])



test_game = Game('01.06.2016', 'OKC', 'MEM')

home_offense_areas, home_defense_areas, away_offense_areas, away_defense_areas = [], [], [], []

for frame in range(len(test_game.moments)):
    offensive_team = test_game.get_offensive_team(frame)
    if offensive_team == 'home':
        home_offense_area, away_defense_area = test_game.get_spacing_area(frame)
        home_offense_areas.append(home_offense_area)
        away_defense_areas.append(away_defense_area)
    if offensive_team == 'away':
        home_defense_area, away_offense_area = test_game.get_spacing_area(frame)
        if home_defense_area > 84:
            print(frame)
        home_defense_areas.append(home_defense_area)
        away_offense_areas.append(away_offense_area)
    if frame % 1000 == 0:
        print(frame)
        

plt.figure()
plt.hist(home_defense_areas, bins=100, alpha=0.4, label=test_game.home_team)
plt.hist(away_defense_areas, bins=100, alpha=0.4, label=test_game.away_team)
plt.xlim(20,100)
plt.legend(loc='upper right')


np.mean(home_defense_areas)
np.mean(away_defense_areas)
