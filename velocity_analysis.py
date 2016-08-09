""""
Analysis of NBA player velocities.
"""

import numpy as np
from scrape import Game
import matplotlib.pyplot as plt
import pickle
import seaborn as sns

"""
One time dump of game:

game = Game('01.01.2016', 'TOR', 'CHA')
pickle.dump(game, open('data/game/temp.p', 'wb'))
"""

game = pickle.load(open('data/game/temp.p', 'rb'))

def calculate_velocities(game, frame):
    if frame == 0:
        return 0 # Need to figure out what to return here (some sort of zero velocity)
    details = game._get_moment_details(frame)
    previous_details = game._get_moment_details(frame - 1)
    if len(details[1]) != 11 or len(details[2]) != 11 or len(previous_details[1]) != 11 or len(previous_details[2]) != 11:
        return 0 # Is this what I actually want to return?
    delta_x = np.array(details[1]) - np.array(previous_details[1])
    delta_y = np.array(details[2]) - np.array(previous_details[2])
    delta_coordinants = zip(delta_x, delta_y)
    distance_traveled = map(lambda coords: np.linalg.norm(coords), delta_coordinants)
    time_frame = 40 #Fix this value (need to update _get_moment_details to include universe time)
    # Note, universe time is in msec, I believe. 
    velocity = map(lambda distances: distances / time_frame, distance_traveled)
    total_velocity = sum(velocity)
    if total_velocity > 0.4:
        return 0
    return total_velocity
    
calculate_velocities(game, 1150)

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
    plt.figtext(0.43, 0.125, shot_clock, size=18)
    plt.figtext(0.5, 0.125, 'Q'+str(quarter), size=18)
    plt.figtext(0.57, 0.125, str(game_clock), size=18)
    plt.figtext(0.43, .454, game.away_team + "  " + score + "  " + game.home_team, size=18)
    if highlight_player:
        plt.figtext(0.17, 0.85, highlight_player, size=18)
    # Add team color indicators to top of frame
    ax.scatter([30, 67], [2.5, 2.5], s=100,
                c=[game.team_colors[game.away_id], game.team_colors[game.home_id]])


def watch_play_velocities(game, start_frame, length):
    end_frame = start_frame + 3 # Need to calculate this properly from length
    indices = list(range(end_frame - start_frame))
    velocities = [calculate_velocities(game, frame) for frame in range(start_frame, end_frame)]
    for index, frame in enumerate(range(start_frame, end_frame)):
        f, (ax1, ax2) = plt.subplots(2, figsize=(12,12))
        plot_velocity_frame(game, frame, ax=ax2)
        ax1.scatter(indices[:index], velocities[:index])
        plt.show()

    
watch_play_velocities(game, 1150, 10)
    
    

game.plot_frame(1150)

    
    
