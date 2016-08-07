import pandas as pd
import pickle
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from spacing_analysis import extract_games
import os



    
game_list = extract_games()

def get_spacing_details(game):
    """
    Writes all spacing statistics to data/spacing directory for every game
    """
    fname = "{game[0]}-{game[2]}-{game[1]}.p".format(game=game)
    if fname in os.listdir('data/spacing') and fname in os.listdir('data/score'):
        data = pickle.load(open( "data/spacing/"+fname, "rb" ))
        score = pickle.load(open( "data/score/"+fname, "rb" )).split(' ')
        away_points, home_points = score[0], score[2]
        means = tuple(map(lambda x: np.mean(x), data))
        if 'GSW' in game:
            print (game, means, home_points, away_points)
        return (int(home_points), int(away_points), *means)
    else:
        return None
    
def get_spacing_df(gamelist):
    details = []
    for game in game_list:
        detail = get_spacing_details(game)
        if detail:
            details.append(detail)
    df = pd.DataFrame(details)
    df.columns = ['home_points', 'away_points', 'home_offense_areas',
                         'home_defense_areas', 'away_offense_areas', 'away_defense_areas']
    return df
    
a = get_spacing_df(game_list)


plt.scatter(a.away_defense_areas, a.home_points)
plt.xlim(55, 75)



