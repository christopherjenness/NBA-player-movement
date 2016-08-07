import pandas as pd
import pickle
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from spacing_analysis import extract_games
import os

test_data = pickle.load(open( "data/spacing/01.10.2016-OKC-POR.p", "rb" ))

plt.scatter(test_data[0], test_data[3])

plt.hist(x=test_data[0], bins = 100, alpha = 0.5)
plt.hist(x=test_data[2], bins = 100, alpha = 0.5)



    
game_list = extract_games()

def get_spacing_means(gamelist):
    """
    Writes all spacing statistics to data/spacing directory for every game
    """
    means = []
    for game in gamelist:
        fname = "{game[0]}-{game[2]}-{game[1]}.p".format(game=game)
        if fname in os.listdir('data/spacing'):
            data = pickle.load(open( "data/spacing/"+fname, "rb" ))
            game_means = tuple(map(lambda x: np.mean(x), data))
            if game_means[0] > 80:
                means.append(game_means)
            else:
                means.append((game_means[1], game_means[0], game_means[3], game_means[2]))
        else: print(fname)
    return means
    
a = get_spacing_means(game_list)

plt.scatter(a[0], a[3])

df = pd.DataFrame(a)

plt.hist(df[0])
first_half = df[df[0]> 80]
second_half = df[df[0] < 80]
plt.scatter(df[0], df[3])
