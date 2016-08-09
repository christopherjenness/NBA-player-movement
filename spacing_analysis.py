"""
Scripts for analyzing spacing of NBA tracking data
"""

import os
import pickle
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn import linear_model
from scrape import Game

def extract_games():
    """
    Extract games from allgames.txt

    Returns:
        list: list of games.  Each element is list is [date, home_team, away_team]
        example element: ['01.01.2016', 'TOR', 'CHI']
    """

    games = []
    with open('allgames.txt', 'r') as game_file:
        for line in game_file:
            game = line.split('.')
            date = "{game[0]}.{game[1]}.{game[2]}".format(game=game)
            away = game[3]
            home = game[5]
            games.append([date, home, away])
    return games

def get_spacing_statistics(date, home_team, away_team, write_file=False,
                           write_score=False, write_game=False):
    """
    Calculates spacing statistics for each frame in game

    Args:
        date (str): date of game in form 'MM.DD.YYYY'.  Example: '01.01.2016'
        home_team (str): home team in form 'XXX'. Example: 'TOR'
        away_team (str): away team in form 'XXX'. Example: 'CHI'
        write_file (bool): If True, write pickle file of spacing statistics into data/spacing directory
        write_score (bool): If True, write pickle file of game score into data/score directory
        write_game (bool): If True, write pickle file of tracking data into data/game directory
            Note: This file is ~100MB.

    Returns:
        tuple: tuple of data (home_offense_areas, home_defense_areas,
               away_offense_areas, away_defense_areas), where each element of the tuple
               is a list of convex hull areas for each frame in the game.
    """
    filename = "{date}-{away_team}-{home_team}.p".format(date=date, away_team=away_team, home_team=home_team)
    # Do not recalculate spacing data if already saved to disk
    if filename in os.listdir('./data/spacing'):
        return
    game = Game(date, home_team, away_team)
    # Write game data to disk
    if write_game:
        pickle.dump(game, open('data/game/' + filename, "wb"))
    home_offense_areas, home_defense_areas = [], []
    away_offense_areas, away_defense_areas = [], []
    print(date, home_team, away_team)
    for frame in range(len(game.moments)):
        offensive_team = game.get_offensive_team(frame)
        if offensive_team:
            home_area, away_area = game.get_spacing_area(frame)
            if offensive_team == 'home':
                home_offense_areas.append(home_area)
                away_defense_areas.append(away_area)
            if offensive_team == 'away':
                home_defense_areas.append(home_area)
                away_offense_areas.append(away_area)
    results = (home_offense_areas, home_defense_areas,
               away_offense_areas, away_defense_areas)
    # Write spacing data to disk
    if write_file:
        filename = "{date}-{away_team}-{home_team}".format(date=date, away_team=away_team, home_team=home_team)
        pickle.dump(results, open('data/spacing/' + filename + '.p', "wb"))
    # Write game scores to disk
    if write_score:
        score = game.pbp['SCORE'].ix[len(game.pbp) - 1]
        pickle.dump(score, open('data/score/' + filename + '.p', "wb"))

    return(home_offense_areas, home_defense_areas,
           away_offense_areas, away_defense_areas)

def write_spacing(gamelist):
    """
    Writes all spacing statistics to data/spacing directory for each game
    """
    for game in gamelist:
        try:
            get_spacing_statistics(game[0], game[1], game[2], write_file=True, write_score=True)
        except:
            with open('errorlog.txt', 'a') as myfile:
                myfile.write("{game} Could not extract spacing data\n".format(game=game))

def plot_spacing(date, home_team, away_team, defense=True, save_plot=False):
    """
    Plots team's spacing distrubution in a game.

    Args:
        date (str): date of game in form 'MM.DD.YYYY'.  Example: '01.01.2016'
        home_team (str): home team in form 'XXX'. Example: 'TOR'
        away_team (str): away team in form 'XXX'. Example: 'CHI'
        defense (bool): if True, plot defensive spacing.  if False, plot offensive spacing
        save_plot (bool): if True, save plot to /temp directory

    Returns: None
        Also, shows plt.hist of team spacing during game

    """
    filename = "{date}-{away_team}-{home_team}".format(date=date, away_team=away_team, home_team=home_team)
    if filename in os.listdir('data/spacing'):
        data = pickle.load(open("data/spacing/"+filename, "rb"))
    else:
        return None
    plt.figure()
    if defense:
        plt.hist(data[1], bins=100, alpha=0.4, label=home_team)
        plt.hist(data[3], bins=100, alpha=0.4, label=away_team)
    else:
        plt.hist(data[0], bins=100, alpha=0.4, label=home_team)
        plt.hist(data[1], bins=100, alpha=0.4, label=away_team)
    plt.xlim(20, 100)
    plt.legend(loc='upper right')
    plt.show()
    if save_plot:
        plt.savefig('temp/spacing{date}.png'.format(date=date))
    return None

def get_spacing_details(game):
    """
    Calculates mean spacing for game.

    Args:
        game (Game): game to compute spacing details for

    Returns: tuple of data  (home_points, away_points, home_offense_areas,
        home_defense_areas, away_offense_areas, away_defense_areas)

        home_points (int): Points scored by home team
        away_points (int): Points scored by away team
        home_offense_area (float): Average spacing (sq ft) of home team while on offense
        home_defense_area (float): Average spacing (sq ft) of home team while on defense
        away_offense_area (float): Average spacing (sq ft) of away team while on offense
        away_defense_area (float): Average spacing (sq ft) of away team while on defense

        if game not saved in data/spacing directory, returns None

    """

    fname = "{game[0]}-{game[2]}-{game[1]}.p".format(game=game)
    if fname in os.listdir('data/spacing') and fname in os.listdir('data/score'):
        data = pickle.load(open("data/spacing/"+fname, "rb"))
        score = pickle.load(open("data/score/"+fname, "rb")).split(' ')
        away_points, home_points = score[0], score[2]
        means = tuple(map(np.mean, data))
        return (int(home_points), int(away_points), *means)
    else:
        return None

def get_spacing_df(gamelist):
    """
    Organizes spacing data from all games into a DataFrame

    Args:
        gamelist (list): list of games where each element [date, home_team, away_team]
            example element: ['01.01.2016', 'TOR', 'CHI']
    Returns: pd.DataFrame
        DataFrame up spacing data with columns: ['home_points', 'away_points',
            'home_offense_areas', 'home_defense_areas', 'away_offense_areas',
            'away_defense_areas', 'away_team', 'home_team', 'space_dif',
            'home_win']
        within DataFrame:
            home_win (int): 1 if home team won, -1 if lost
            space_dif (float): difference (sq ft) between away team's defensive spacing
                and home team's defensive spacing
    """

    details = []
    for game in gamelist:
        detail = get_spacing_details(game)
        if detail:
            details.append((*detail, game[1], game[2]))
    df = pd.DataFrame(details)
    df.columns = ['home_points', 'away_points', 'home_offense_areas',
                  'home_defense_areas', 'away_offense_areas',
                  'away_defense_areas', 'away_team', 'home_team']
    df['space_dif'] = df.away_defense_areas - df.home_defense_areas
    df['home_win'] = np.sign(df.home_points - df.away_points)
    df = df[df.home_offense_areas > 80]
    return df

def plot_offense_vs_defense_spacing(spacing_data, save_fig=False):
    """
    Plot of offensive vs. defensive spacing for games

    Args:
        spacing_data (pd.DataFrame): Dataframe with columns of spacing data
            ['home_offense_areas', 'home_defense_areas',
             'away_offense_areas', 'away_defense_areas']
        save_fig (bool): if True, save plot to temp/ directory

    Returns None
        Also, shows plot.
    """
    sns.regplot(spacing_data.away_offense_areas, spacing_data.home_defense_areas,
                fit_reg=True, color=sns.color_palette()[0], ci=None)
    sns.regplot(spacing_data.home_offense_areas, spacing_data.away_defense_areas,
                fit_reg=False, color=sns.color_palette()[0], ci=None)
    plt.xlabel('Average Offensive Spacing (sq ft)', fontsize=16)
    plt.ylabel('Average Defensive Spacing (sq ft)', fontsize=16)
    plt.title('Offensive spacing robustly induces defensive spacing', fontsize=16)
    plt.show()
    if save_fig:
        plt.savefig('temp/OffenseVsDefense.png')
    return None

def plot_defense_spacing_vs_score(spacing_data, save_fig=False):
    """
    Plot of team's defensive spacing vs score differential for games

    Args:
        spacing_data (pd.DataFrame): Dataframe with columns of spacing data
            ['home_offense_areas', 'home_defense_areas',
             'away_offense_areas', 'away_defense_areas']
        save_fig (bool): if True, save plot to temp/ directory

    Returns None
        Also, shows plot.
    """

    y = spacing_data.home_points - spacing_data.away_points
    x = spacing_data.away_defense_areas - spacing_data.home_defense_areas
    sns.regplot(x, y, ci=False)
    plt.xlabel(' Home Team Defensive Spacing Differential (sq ft)', fontsize=16)
    plt.ylabel('Home Team Score Differential (pts)', fontsize=16)
    plt.title('Spacing the defense correlates with outscoring opponents', fontsize=16)
    plt.show()
    if save_fig:
        plt.savefig('temp/SpacingVsScore.png')

def plot_defense_spacing_vs_wins(spacing_data, save_fig=False):
    """
    Plot of team's defensive spacing vs wins (binary: 0, 1) for games

    Args:
        spacing_data (pd.DataFrame): Dataframe with columns of spacing data
            ['home_offense_areas', 'home_defense_areas',
             'away_offense_areas', 'away_defense_areas']
        save_fig (bool): if True, save plot to temp/ directory

    Returns None
        Also, shows plot.
    """

    clf = linear_model.LogisticRegression(C=1)
    X = np.array(spacing_data.space_dif)
    X = X[:, np.newaxis]
    y = np.array(spacing_data.home_win)
    y_adjusted = (y+1) / 2
    clf.fit(X, y)
    plt.scatter(X.ravel(), y_adjusted, color=sns.color_palette()[0],
                s=600, alpha=1, marker='|')
    plt.xlim(-10, 10)
    X_test = np.linspace(-10, 10, 300)
    X_test = X_test[:, np.newaxis]
    clf.predict(X_test)
    def model(x):
        return 1 / (1 + np.exp(-x))
    log_fit = model(X_test * clf.coef_ + clf.intercept_).ravel()
    plt.scatter(X_test.ravel(), log_fit)
    plt.xlabel('Home Team Defensive Spacing Differential (sq ft)', fontsize=16)
    plt.ylabel('Home Team Win', fontsize=16)
    plt.title('Spacing the Defense Correlates with winning', fontsize=16)
    plt.show()
    if save_fig:
        plt.savefig('temp/SpacingVsWins.png')

def plot_team_defensive_spacing(spacing_data, save_fig=False):
    """
    Plot of team's defensive spacing (bar graph)

    Args:
        spacing_data (pd.DataFrame): Dataframe with columns of spacing data
            ['home_offense_areas', 'home_defense_areas',
             'away_offense_areas', 'away_defense_areas']
        save_fig (bool): if True, save plot to temp/ directory

    Returns None
        Also, shows plot.
    """

    df = pd.DataFrame()
    df['home'] = spacing_data.groupby('home_team')['away_defense_areas'].sum()
    df['home_count'] = spacing_data.groupby('home_team')['away_defense_areas'].count()
    df['away'] = spacing_data.groupby('away_team')['home_defense_areas'].sum()
    df['away_count'] = spacing_data.groupby('away_team')['home_defense_areas'].count()
    df['average_induced_space'] = (df.home + df.away) / (df.away_count + df.home_count)
    df['average_induced_space'].sort_values().plot(kind='bar', color=sns.color_palette()[0])
    plt.xlabel('Team', fontsize=16)
    plt.ylabel("Opponent's Defensive Spacing", fontsize=16)
    plt.ylim(60, 70)
    plt.show()
    if save_fig:
        plt.savefig('temp/DefensiveSpacing.png')

def plot_teams_ability_to_space_defense(spacing_data, save_fig=False):
    """
    Plots teams ability to space defense given their offensive spacing (scatter plot)

    Args:
        spacing_data (pd.DataFrame): Dataframe with columns of spacing data
            ['home_offense_areas', 'home_defense_areas',
             'away_offense_areas', 'away_defense_areas']
        save_fig (bool): if True, save plot to temp/ directory

    Returns None
        Also shows plot
    """

    df = spacing_data.groupby('home_team').count()
    df['home'] = spacing_data.groupby('home_team')['away_defense_areas'].sum()
    df['home_count'] = spacing_data.groupby('home_team')['away_defense_areas'].count()
    df['away'] = spacing_data.groupby('away_team')['home_defense_areas'].sum()
    df['away_count'] = spacing_data.groupby('away_team')['home_defense_areas'].count()
    df['average_induced_space'] = (df.home + df.away) / (df.away_count + df.home_count)

    df['home_offense'] = spacing_data.groupby('home_team')['home_offense_areas'].sum()
    df['home_offense_count'] = spacing_data.groupby('home_team')['home_offense_areas'].count()
    df['away_offense'] = spacing_data.groupby('away_team')['away_offense_areas'].sum()
    df['away_offense_count'] = spacing_data.groupby('away_team')['away_offense_areas'].count()
    df['average_offense_space'] = (df.home_offense + df.away_offense) / (df.away_offense_count + df.home_offense_count)
    plt.scatter(df['average_induced_space'], df['average_offense_space'], s=74, alpha=0.7, c=sns.color_palette()[0])
    for row in df.iterrows():
        if row[0] in ['DEN', 'SAS', 'LAC', 'CLE', 'DET', 'WAS', 'TOR', 'MIL', 'ORL', 'DAL']:
            plt.annotate(row[0],
                         xy=[row[1]['average_induced_space'] + -0.15,
                             row[1]['average_offense_space'] + 0.1])
    plt.xlabel('Average Offensive Spacing (sq ft)', fontsize=16)
    plt.ylabel("Average Opponent's Defensive Spacing (sq ft)", fontsize=16)
    plt.title("Team's ability to space opponents defense", fontsize=16)
    plt.show()
    if save_fig:
        plt.savefig('temp/Spacing_scatter.png')

if __name__ == "__main__":
    """
    Calls functions to generate plots.  Uncomment lines which you want to plot.
    if spacing data has not been calculated, uncomment 'write_spacing(games)', which
    will calculate the spacing data for all games and save it to disk.
    """

    all_games = extract_games()
    #write_spacing(all_games)
    spacing_data = get_spacing_df(all_games)
    #plot_offense_vs_defense_spacing(spacing_data)
    #plot_defense_spacing_vs_score(spacing_data)
    #plot_defense_spacing_vs_wins(spacing_data)
    #plot_team_defensive_spacing(spacing_data)
    #plot_teams_ability_to_space_defense(spacing_data)
