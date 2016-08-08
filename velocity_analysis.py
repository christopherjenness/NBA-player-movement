""""
Analysis of NBA player velocities.
"""

import numpy as np
from scrape import Game
import matplotlib.pyplot as plt

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

def watch_play_velocities(game, start_frame, length):
    end_frame = start_frame + 1000
    indices = list(range(end_frame - start_frame))
    velocities = [calculate_velocities(game, frame) for frame in range(start_frame, end_frame)]
    game.plot_frame(start_frame)
    plt.scatter(indices, velocities)

    
watch_play_velocities(game, 1150, 1)
    
    

    
    
    
