""""
Analysis of NBA player velocities.

TODO: 
- Show player annotation somewhere when highlight_player
- individual player velocities
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

"""
One time dump of game:

game = Game('01.01.2016', 'TOR', 'CHA')
pickle.dump(game, open('data/game/temp.p', 'wb'))
"""

game = pickle.load(open('data/game/temp.p', 'rb'))

def calculate_velocities(game, frame, highlight_player=None):
    """
    
    """
    details = game._get_moment_details(frame, highlight_player=highlight_player)
    previous_details = game._get_moment_details(frame - 1)
    
    # Highlighed player's edge value (details[8]) is 5 instead of 0.5
    # Use this fact to retrieve the index of the player
    
    if highlight_player:
        if 5 in details[8]:
            player_index = details[8].index(5)
        else:
            highlight_player=None
            
    if frame == 0:
        if highlight_player:
            return 0
        return (0, 0)

    if len(details[1]) != 11 or len(details[2]) != 11 or len(previous_details[1]) != 11 or len(previous_details[2]) != 11:
        return 0
    delta_x = np.array(details[1]) - np.array(previous_details[1])
    delta_y = np.array(details[2]) - np.array(previous_details[2])
    delta_coordinants = zip(delta_x, delta_y)
    distance_traveled = map(lambda coords: np.linalg.norm(coords), delta_coordinants)
    time_frame = 40 #Fix this value (need to update _get_moment_details to include universe time)
    # Note, universe time is in msec
    velocity = list(map(lambda distances: distances / time_frame, distance_traveled))
    if highlight_player:
        return velocity[player_index]
    # Check if home team and away team are assigned correctly
    home_velocity = sum(velocity[1:6])
    away_velocity = sum(velocity[6:])
    # Fix the following numbers
    if home_velocity > 0.4:
        home_velocity = 0
    if away_velocity > 0.4:
        away_velocity = 0
    return (home_velocity, away_velocity)

calculate_velocities(game, 10, highlight_player='Nicolas Batum')

def plot_velocity_frame(game, frame_number, ax, highlight_player=None):
    """
    Creates an individual the frame of game.

    Args:
        game (Game): Game instance to get data from
        frame_number (int): number of frame in game to create
            frame_number gets player tracking data from moments.ix[frame_number]
        highlight_player (str): Name of player to highlight (by making their outline thicker).
            if None, no player is highlighted

    Returns: plt.fig of frame from game
    """
    (game_time, x_pos, y_pos, colors, sizes, quarter, shot_clock, game_clock, edges) = game._get_moment_details(frame_number, highlight_player=highlight_player)
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
    
    starting_frame = game.moments[game.moments.game_time.round() == game_time].index.values[0]
    ending_frame = game.moments[game.moments.game_time.round() == game_time + length].index.values[0]
        
    indices = list(range(ending_frame - starting_frame))
    
    if highlight_player:
        player_velocities = [calculate_velocities(game, frame, highlight_player=highlight_player) for frame in range(starting_frame, ending_frame)]
        max_velocity = max(player_velocities)
    else:
        home_velocities = [calculate_velocities(game, frame)[0] for frame in range(starting_frame, ending_frame)]
        away_velocities = [calculate_velocities(game, frame)[1] for frame in range(starting_frame, ending_frame)]
        max_velocity = max(home_velocities + away_velocities)
    
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

def get_velocity_statistics(date, home_team, away_team, write_file=False,
                           write_score=False, write_game=False):
    """
    Calculates velocity statistics for each frame in game

    Args:
        date (str): date of game in form 'MM.DD.YYYY'.  Example: '01.01.2016'
        home_team (str): home team in form 'XXX'. Example: 'TOR'
        away_team (str): away team in form 'XXX'. Example: 'CHI'
        write_file (bool): If True, write pickle file of spacing statistics into data/velocity directory
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
    for frame in range(len(game.moments)):
        offensive_team = game.get_offensive_team(frame)
        if offensive_team:
            home_velocity, away_velocity = calculate_velocities(game, frame)
            if offensive_team == 'home':
                home_offense_velocities.append(home_velocity)
                away_defense_velocities.append(away_velocity)
            if offensive_team == 'away':
                home_defense_velocities.append(home_velocity)
                away_offense_velocities.append(away_velocity)
    results = (home_offense_velocities, home_defense_velocities,
               away_offense_velocities, away_defense_velocities)
    # Write spacing data to disk
    if write_file:
        filename = "{date}-{away_team}-{home_team}".format(date=date, away_team=away_team, home_team=home_team)
        pickle.dump(results, open('data/velocity/' + filename + '.p', "wb"))
    # Write game scores to disk
    if write_score:
        score = game.pbp['SCORE'].ix[len(game.pbp) - 1]
        pickle.dump(score, open('data/score/' + filename + '.p', "wb"))

    return (home_offense_velocities, home_defense_velocities,
            away_offense_velocities, away_defense_velocities)

    
#watch_play_velocities(game, 52, 2, highlight_player='Nicolas Batum')
#watch_play_velocities(game, 53, 2)


    
    












