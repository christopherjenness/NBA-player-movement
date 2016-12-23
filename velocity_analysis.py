""""
Analysis of NBA player velocities.

TODO: 
- analysis
- 1st vs 4th quarter? (measure of tiredness) - compare points made in 1st vs 4th quarter
- compare velocities before made and missed shots
- display a no-velocity vs high-velocity play
"""

import numpy as np
from game import Game
import matplotlib.pyplot as plt
import pickle
import seaborn as sns
import os

#Initialize Project
os.chdir('/Users/christopherjenness/Desktop/Personal/SportVU/NBA-player-movement')

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

def calculate_velocities(game, frame, highlight_player=None):
    """
    Calculates team or player velocity for a frame in a game
    
    Args:
        game (Game): Game instance to get data from
        frame_number (int): number of frame in game to calculate velocities
            frame_number gets player tracking data from moments.ix[frame_number]
        highlight_player (str): Name of player to calculate velocity of.
            if None, cumulative team velocities are calculated.
    
    Returns: tuple of data (game_time, home_velocity, away_velocity)
        game_time (int): universe time of the frame
        home_velocity (float): cumulative velocity (ft/msec) of home team
        away_velocity (float): cumulative velocity (ft/msec) of away team
    """
    details = game._get_moment_details(frame, highlight_player=highlight_player)
    previous_details = game._get_moment_details(frame - 1)
    game_time = details[9]
    
    # Highlighed player's edge value (details[8]) is 5 instead of 0.5
    # Use this fact to retrieve the index of the player of interest
    if highlight_player:
        if 5 in details[8]:
            player_index = details[8].index(5)
        else:
            highlight_player=None
            
    if frame == 0:
        if highlight_player:
            return 0
        return (game_time, 0, 0)

    # If not all the players are on the court, there is an error in the data
    if len(details[1]) != 11 or len(details[2]) != 11 or len(previous_details[1]) != 11 or len(previous_details[2]) != 11:
        return (game_time, 0, 0)
    delta_x = np.array(details[1]) - np.array(previous_details[1])
    delta_y = np.array(details[2]) - np.array(previous_details[2])
    delta_coordinants = zip(delta_x, delta_y)
    distance_traveled = map(lambda coords: np.linalg.norm(coords), delta_coordinants)
    delta_time = details[9] - previous_details[9]
    # Note, universe time is in msec
    velocity = list(map(lambda distances: distances / delta_time, distance_traveled))
    if highlight_player:
        return (game_time, velocity[player_index])
    home_velocity = sum(velocity[1:6])
    away_velocity = sum(velocity[6:])
    return (game_time, home_velocity, away_velocity)

def plot_velocity_frame(game, frame_number, ax, highlight_player=None):
    """
    Creates an individual the frame of game.

    Args:
        game (Game): Game instance to get data from
        frame_number (int): number of frame in game to create
            frame_number gets player tracking data from moments.ix[frame_number]
        highlight_player (str): Name of player to highlight (by making their outline thicker).
            if None, no player is highlighted

    Returns: plt.fig of frame from game with subplot of velocity.
        see README.md for example
    """
    (game_time, x_pos, y_pos, colors, sizes, quarter, shot_clock, game_clock, edges, universe_time) = game._get_moment_details(frame_number, highlight_player=highlight_player)
    (commentary_script, score) = game._get_commentary(game_time)
    
    game._draw_court()
    frame = plt.gca()
    frame.axes.get_xaxis().set_ticks([])
    frame.axes.get_yaxis().set_ticks([])
    ax.scatter(x_pos, y_pos, c=colors, s=sizes, alpha=0.85, linewidths=edges)
    plt.xlim(-5, 100)
    plt.ylim(-55, 5)
    sns.set_style('dark')
    plt.figtext(0.43, 0.105, shot_clock, size=18)
    plt.figtext(0.5, 0.105, 'Q'+str(quarter), size=18)
    plt.figtext(0.57, 0.105, str(game_clock), size=18)
    plt.figtext(0.43, .442, game.away_team + "  " + score + "  " + game.home_team, size=18)

    # Add team color indicators to top of frame
    ax.scatter([30, 67], [2.5, 2.5], s=100,
                c=[game.team_colors[game.away_id], game.team_colors[game.home_id]])


def watch_play_velocities(game, game_time, length, highlight_player=None):
    """
    Creates an movie of a play which includes a plot of the real-time velocities.

    Args:
        game (Game): Game instance to get data from
        game_time (int): time in game to start video (seconds into the game).
        length (int): length of play to watch (seconds)
        highlight_player (str): If not None, video will highlight the circle of
            the inputed player for easy tracking, and also display that players velocity

    Returns: an instance of self, and outputs video file of play with velocity plot
        see README.md for example
    """
    starting_frame = game.moments[game.moments.game_time.round() == game_time].index.values[0]
    ending_frame = game.moments[game.moments.game_time.round() == game_time + length].index.values[0]
        
    indices = list(range(ending_frame - starting_frame))
    
    if highlight_player:
        player_velocities = [calculate_velocities(game, frame, highlight_player=highlight_player)[1] for frame in range(starting_frame, ending_frame)]
        max_velocity = max(player_velocities)
    else:
        home_velocities = [calculate_velocities(game, frame)[1] for frame in range(starting_frame, ending_frame)]
        away_velocities = [calculate_velocities(game, frame)[2] for frame in range(starting_frame, ending_frame)]
        all_velocities =  home_velocities + away_velocities
        max_velocity = max(all_velocities)
    
    # Plot each frame
    for index, frame in enumerate(range(starting_frame, ending_frame)):
        f, (ax1, ax2) = plt.subplots(2, figsize=(12,12))
        plot_velocity_frame(game, frame, ax=ax2, highlight_player=highlight_player)
        ax1.set_xlim([0, len(indices)])
        ax1.set_ylim([0, max_velocity * 1.2]) 
        if highlight_player:
            ax1.plot(indices[:index+1], player_velocities[:index+1], c='black', label=highlight_player)
        else:
            ax1.plot(indices[:index+1], home_velocities[:index+1], c=game.team_colors[game.home_id], label=game.home_team)
            ax1.plot(indices[:index+1], away_velocities[:index+1], c=game.team_colors[game.away_id], label=game.away_team)
        ax1.set_yticklabels([])
        ax1.set_xticklabels([])
        ax1.set_ylabel('Velocity', fontsize=22)
        if highlight_player:
            ax1.set_title(highlight_player, fontsize=24)
        else:
            ax1.legend(fontsize=18)
        plt.savefig('temp/' + str(index) + '.png')
        plt.close()

    # Make video of each frame
    command = 'ffmpeg -framerate 20 -start_number 0 -i %d.png -c:v libx264 -r 30 -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" {starting_frame}.mp4'.format(starting_frame=starting_frame)
    os.chdir('temp')
    os.system(command)
    os.chdir('..')

    #Delete images
    for file in os.listdir('./temp'):
        if os.path.splitext(file)[1] == '.png':
            os.remove('./temp/{file}'.format(file=file))

    return self

def get_velocity_statistics(date, home_team, away_team, write_file=False,
                           write_score=False, write_game=False):
    """
    Calculates velocity statistics for each frame in game

    Args:
        date (str): date of game in form 'MM.DD.YYYY'.  Example: '01.01.2016'
        home_team (str): home team in form 'XXX'. Example: 'TOR'
        away_team (str): away team in form 'XXX'. Example: 'CHI'
        write_file (bool): If True, write pickle file of velocity statistics into data/velocity directory
        write_score (bool): If True, write pickle file of game score into data/score directory
        write_game (bool): If True, write pickle file of tracking data into data/game directory
            Note: This file is ~100MB.

    Returns:
        tuple: tuple of data (home_offense_velocities, home_defense_velocities,
               away_offense_velocities, away_defense_velocities), where each element of the tuple
               is a list of tuples (frame, game_time, velocity) for each frame in the game.
    """
    filename = "{date}-{away_team}-{home_team}.p".format(date=date, away_team=away_team, home_team=home_team)
    # Do not recalculate spacing data if already saved to disk
    if filename in os.listdir('./data/velocity/'):
        return
    game = Game(date, home_team, away_team)
    # Write game data to disk
    if write_game:
        pickle.dump(game, open('data/game/' + filename, "wb"))
    home_offense_velocities, home_defense_velocities = [], []
    away_offense_velocities, away_defense_velocities = [], []
    print(date, home_team, away_team)
    for frame in range(1, len(game.moments)):
        offensive_team = game.get_offensive_team(frame)
        if offensive_team:
            game_time, home_velocity, away_velocity = calculate_velocities(game, frame)
            if offensive_team == 'home':
                home_offense_velocities.append((frame, game_time, home_velocity))
                away_defense_velocities.append((frame, game_time, away_velocity))
            if offensive_team == 'away':
                home_defense_velocities.append((frame, game_time, home_velocity))
                away_offense_velocities.append((frame, game_time, away_velocity))
    results = (home_offense_velocities, home_defense_velocities,
               away_offense_velocities, away_defense_velocities)
    # Write velocity data to disk
    if write_file:
        filename = "{date}-{away_team}-{home_team}".format(date=date, away_team=away_team, home_team=home_team)
        pickle.dump(results, open('data/velocity/' + filename + '.p', "wb"))
    # Write game scores to disk
    if write_score:
        score = game.pbp['SCORE'].ix[len(game.pbp) - 1]
        pickle.dump(score, open('data/score/' + filename + '.p', "wb"))

    return (home_offense_velocities, home_defense_velocities,
            away_offense_velocities, away_defense_velocities)

def write_velocity(gamelist):
    """
    Writes all spacing statistics to data/spacing directory for each game
    """
    for game in gamelist:
        try:
            get_velocity_statistics(game[0], game[1], game[2], write_file=True, write_score=True)
        except:
            with open('errorlog_velocity.txt', 'a') as myfile:
                myfile.write("{game} Could not extract velocity data\n".format(game=game))
                
def analyze_velocity(gamelist):
    for game in gamelist:
        filename = "{date}-{away_team}-{home_team}".format(date=game[0], away_team=game[2], home_team=game[1])
        try:
            velocity_data = pickle.load(open('data/velocity/12.31.2015-POR-UTA.p', 'rb'))
            home_offense_velocities = pd.DataFrame(velocity_data[0])
            home_defense_velocities = pd.DataFrame(velocity_data[1])
            away_offense_velocities = pd.DataFrame(velocity_data[2])
            away_defense_velocities = pd.DataFrame(velocity_data[3])
        except:
            print ('velocity data not written for: ', game)
if __name__ == "__main__":
    """
    """

    all_games = extract_games()
    write_velocity(all_games)
    #spacing_data = get_spacing_df(all_games)

"""
import pickle 
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
test = pickle.load(open('data/velocity/12.31.2015-POR-UTA.p', 'rb'))
type(test)


df = pd.DataFrame(test[0])
plt.plot(df[0], df[2])
df[2].mean()
"""
