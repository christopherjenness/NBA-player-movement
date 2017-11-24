""""
Analysis of NBA player velocities.
"""

import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from game import Game

# Initialize Project
os.chdir('~/Desktop/Personal/SportVU/NBA-player-movement')


def extract_games():
    """
    Extract games from allgames.txt

    Returns:
        list: list of games.  Each element is list is tuple
            (date, home_team, away_team)
        example element: ('01.01.2016', 'TOR', 'CHI')
    """

    games = []
    with open('allgames.txt', 'r') as game_file:
        for line in game_file:
            game = line.split('.')
            date = "{game[0]}.{game[1]}.{game[2]}".format(game=game)
            away = game[3]
            home = game[5]
            games.append((date, home, away))
    return games


def calculate_velocities(game, frame, highlight_player=None):
    """
    Calculates team or player velocity for a frame in a game

    Args:
        game (Game): Game instance to get data from
        frame_number (int): number of frame in game to calculate velocities
            frame_number gets player tracking data from moments.ix[frame]
        highlight_player (str): Name of player to calculate velocity of.
            if None, cumulative team velocities are calculated.

    Returns: tuple of data (game_time, home_velocity, away_velocity)
        game_time (int): universe time of the frame
        home_velocity (float): cumulative velocity (ft/msec) of home team
        away_velocity (float): cumulative velocity (ft/msec) of away team
    """
    details = game._get_moment_details(frame,
                                       highlight_player=highlight_player)
    previous_details = game._get_moment_details(frame - 1)
    game_time = details[9]

    # Highlighed player's edge value (details[8]) is 5 instead of 0.5
    # Use this fact to retrieve the index of the player of interest
    if highlight_player:
        if 5 in details[8]:
            player_index = details[8].index(5)
        else:
            highlight_player = None

            if frame == 0:
                if highlight_player:
                    return 0
                return (game_time, 0, 0)

    # If not all the players are on the court, there is an error in the data
    if len(details[1]) != 11 or \
       len(details[2]) != 11 or \
       len(previous_details[1]) != 11 or \
       len(previous_details[2]) != 11:
        return (game_time, 0, 0)

    delta_x = np.array(details[1]) - np.array(previous_details[1])
    delta_y = np.array(details[2]) - np.array(previous_details[2])
    delta_coordinants = zip(delta_x, delta_y)
    distance_traveled = map(lambda coords: np.linalg.norm(coords),
                            delta_coordinants)
    delta_time = details[9] - previous_details[9]
    # Note, universe time is in msec
    velocity = list(map(lambda distances: distances / delta_time,
                        distance_traveled))
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
            frame_number gets player tracking data from
            moments.ix[frame_number]
        highlight_player (str): Name of player to highlight (by making
            their outline thicker).
            if None, no player is highlighted

    Returns: plt.fig of frame from game with subplot of velocity.
        see README.md for example
    """
    (game_time, x_pos, y_pos, colors, sizes,
     quarter, shot_clock, game_clock, edges,
     universe_time) = game._get_moment_details(frame_number,
                                               highlight_player=highlight_player)
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
    plt.figtext(0.43, .442,
                game.away_team + "  " + score + "  " + game.home_team,
                size=18)

    # Add team color indicators to top of frame
    ax.scatter([30, 67], [2.5, 2.5], s=100,
               c=[game.team_colors[game.away_id],
                  game.team_colors[game.home_id]])


def watch_play_velocities(game, game_time, length, highlight_player=None):
    """
    Creates an movie of a play which includes a plot of the
        real-time velocities.

    Args:
        game (Game): Game instance to get data from
        game_time (int): time in game to start video (seconds into the game).
        length (int): length of play to watch (seconds)
        highlight_player (str): If not None, video will highlight the circle of
            the inputed player for easy tracking, and also display that
            players velocity

    Returns: an instance of self, and outputs video file of play with
        velocity plot see README.md for example
    """
    starting_frames = game.moments[game.moments.game_time.round() ==
                                   game_time]
    starting_frame = starting_frames.index.values[0]
    ending_frames = game.moments[game.moments.game_time.round() ==
                                 game_time + length]
    ending_frame = ending_frames.index.values[0]

    indices = list(range(ending_frame - starting_frame))

    if highlight_player:
        player_velocities = [calculate_velocities(game, frame,
                                                  highlight_player=highlight_player)[1]
                             for frame in range(starting_frame, ending_frame)]
        max_velocity = max(player_velocities)
    else:
        home_velocities = [calculate_velocities(game, frame)[1]
                           for frame in range(starting_frame, ending_frame)]
        away_velocities = [calculate_velocities(game, frame)[2]
                           for frame in range(starting_frame, ending_frame)]
        all_velocities = home_velocities + away_velocities
        max_velocity = max(all_velocities)

    # Plot each frame
    for index, frame in enumerate(range(starting_frame, ending_frame)):
        f, (ax1, ax2) = plt.subplots(2, figsize=(12, 12))
        plot_velocity_frame(game, frame, ax=ax2,
                            highlight_player=highlight_player)
        ax1.set_xlim([0, len(indices)])
        ax1.set_ylim([0, max_velocity * 1.2])
        if highlight_player:
            ax1.plot(indices[:index+1], player_velocities[:index+1],
                     c='black', label=highlight_player)
        else:
            ax1.plot(indices[:index+1], home_velocities[:index+1],
                     c=game.team_colors[game.home_id], label=game.home_team)
            ax1.plot(indices[:index+1], away_velocities[:index+1],
                     c=game.team_colors[game.away_id], label=game.away_team)
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
    command = ('ffmpeg -framerate 20 -start_number 0 -i %d.png -c:v '
               'libx264 -r 30 -pix_fmt yuv420p -vf '
               '"scale=trunc(iw/2)*2:trunc(ih/2)*2" {starting_frame}'
               '.mp4').format(starting_frame=starting_frame)
    os.chdir('temp')
    os.system(command)
    os.chdir('..')

    # Delete images
    for file in os.listdir('./temp'):
        if os.path.splitext(file)[1] == '.png':
            os.remove('./temp/{file}'.format(file=file))

    return


def get_velocity_statistics(date, home_team, away_team, write_file=False,
                            write_score=False, write_game=False):
    """
    Calculates velocity statistics for each frame in game

    Args:
        date (str): date of game in form 'MM.DD.YYYY'.  Example: '01.01.2016'
        home_team (str): home team in form 'XXX'. Example: 'TOR'
        away_team (str): away team in form 'XXX'. Example: 'CHI'
        write_file (bool): If True, write pickle file of velocity
            statistics into data/velocity directory
        write_score (bool): If True, write pickle file of game score
            into data/score directory
        write_game (bool): If True, write pickle file of tracking data
            into data/game directory
            Note: This file is ~100MB.

    Returns:
        tuple: tuple of data (home_offense_velocities, home_defense_velocities,
               away_offense_velocities, away_defense_velocities), where each
               element of the tuple is a list of tuples
               (frame, game_time, velocity) for each frame in the game.
    """
    filename = ("{date}-{away_team}-"
                "{home_team}.p").format(date=date, away_team=away_team,
                                        home_team=home_team)
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
            (game_time, home_velocity,
             away_velocity) = calculate_velocities(game, frame)
            if offensive_team == 'home':
                home_offense_velocities.append((frame, game_time,
                                                home_velocity))
                away_defense_velocities.append((frame, game_time,
                                                away_velocity))
            if offensive_team == 'away':
                home_defense_velocities.append((frame, game_time,
                                                home_velocity))
                away_offense_velocities.append((frame, game_time,
                                                away_velocity))
    results = (home_offense_velocities, home_defense_velocities,
               away_offense_velocities, away_defense_velocities)
    # Write velocity data to disk
    if write_file:
        filename = ("{date}-{away_team}-"
                    "{home_team}").format(date=date,
                                          away_team=away_team,
                                          home_team=home_team)
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
            get_velocity_statistics(game[0], game[1], game[2],
                                    write_file=True, write_score=True)
        except:
            with open('errorlog_velocity.txt', 'a') as myfile:
                myfile.write("{game} Could not extract velocity data\n"
                             .format(game=game))


def extract_velocity(gamelist):
    """
    Loads velocity data, calculates average offensive and defensive
        velocity for each game in gamelist
        Note: requires velocity data to be written for each game in
        data/velocity and data/score (see get_velocity_statistics())

    Args:
        gamelist (list):  list of games.  Each element is list is tuple
            (date, home_team, away_team).
            example element: ('01.01.2016', 'TOR', 'CHI')

    Returns (pd.DataFrame): Dataframe of velocity data with columns:
        0: Home Offensive Velocity
        1: Away Offensive Velocity
        2: Home Defensive Velocity
        3: Away Defensive Velocity
        4: Away Score
        5: Home Score
        6: Away Team
        7: Home Team
    """
    data = []
    for game in gamelist:
        away_team = game[2]
        home_team = game[1]
        print(away_team, home_team)
        filename = ("{date}-{away_team}-"
                    "{home_team}").format(date=game[0],
                                          away_team=away_team,
                                          home_team=home_team)

        # Load velocity/score data
        try:
            velocity_data = pickle.load(open('data/velocity/'
                                             + filename + '.p',
                                             'rb'))
            score_data = pickle.load(open('data/score/'
                                          + filename + '.p',
                                          'rb'))
        except:
            print('velocity data not written for: ', game)
            continue

        away_score, home_score = extract_scores(score_data)
        # Organize velocity data by team and offense/defense
        HOV = pd.DataFrame(velocity_data[0])
        HDV = pd.DataFrame(velocity_data[1])
        AOV = pd.DataFrame(velocity_data[2])
        ADV = pd.DataFrame(velocity_data[3])

        # Cut out erroneous velocity data
        # This is due to Frame-skipping in the SVU data
        # For example, from the last frame of a quarter to the
        # first frame of the next quarter, etc.
        HOV = HOV[HOV[2] < 0.15]
        AOV = AOV[AOV[2] < 0.15]
        HDV = HDV[HDV[2] < 0.15]
        ADV = ADV[ADV[2] < 0.15]

        game_data = (HOV[2].mean(), AOV[2].mean(), HDV[2].mean(),
                     ADV[2].mean(), away_score, home_score, away_team,
                     home_team)
        data.append(game_data)
    return pd.DataFrame(data)


def extract_fatigue(gamelist):
    """
    Loads velocity data, calculates average offensive and defensive
        velocity for each quarter for each game in gamelist
        Note: requires velocity data to be written for each game in
        data/velocity and data/score (see get_velocity_statistics())

    Args:
        gamelist (list):  list of games.  Each element is list is tuple
            (date, home_team, away_team).
            example element: ('01.01.2016', 'TOR', 'CHI')

    Returns (pd.DataFrame): Dataframe of velocity data with columns:
        Tm: team
        Pos: Offense or Defense
        1: 1st Quarter Mean Velocity
        2: 2nd Quarter Mean Velocity
        3: 3rd Quarter Mean Velocity
        4: 4th Quarter Mean Velocity
    """
    data = []
    for game in gamelist:
        away_team = game[2]
        home_team = game[1]
        print(away_team, home_team)
        filename = ("{date}-{away_team}-"
                    "{home_team}").format(date=game[0],
                                          away_team=away_team,
                                          home_team=home_team)

        # Load velocity/score data
        try:
            velocity_data = pickle.load(open('data/velocity/'
                                             + filename + '.p',
                                             'rb'))
            score_data = pickle.load(open('data/score/'
                                          + filename + '.p',
                                          'rb'))
        except:
            print('velocity data not written for: ', game)
            continue

        away_score, home_score = extract_scores(score_data)
        # Organize velocity data by team and offense/defense
        HOV = pd.DataFrame(velocity_data[0])
        HDV = pd.DataFrame(velocity_data[1])
        AOV = pd.DataFrame(velocity_data[2])
        ADV = pd.DataFrame(velocity_data[3])

        # Cut out erroneous velocity data
        # This is due to Frame-skipping in the SVU data
        # For example, from the last frame of a quarter to the
        # first frame of the next quarter, etc.
        HOV = HOV[HOV[2] < 0.15]
        AOV = AOV[AOV[2] < 0.15]
        HDV = HDV[HDV[2] < 0.15]
        ADV = ADV[ADV[2] < 0.15]

        quarter_velocities = {}
        for quarter in [1, 2, 3, 4]:
            ending_frame = int(len(HOV)/4 * quarter)
            starting_frame = int(len(HOV)/4 * (quarter-1))

            quarter_velocities[quarter] = [HOV.iloc[starting_frame:
                                                    ending_frame][2].mean(),
                                           HDV.iloc[starting_frame:
                                                    ending_frame][2].mean(),
                                           AOV.iloc[starting_frame:
                                                    ending_frame][2].mean(),
                                           ADV.iloc[starting_frame:
                                                    ending_frame][2].mean(),
                                           ]
        df = pd.DataFrame(quarter_velocities)
        df['Tm'] = [home_team, home_team, away_team, away_team]
        df['Pos'] = ['Off', 'Def', 'Off', 'Def']

        game_data = (df, away_score, home_score, away_team, home_team)
        data.append(game_data)
    df = pd.DataFrame()
    for i in range(len(data)):
        df = pd.concat((df, data[i][0]))
    df = pd.melt(df, ['Tm', 'Pos'], [1, 2, 3, 4])
    return df


def velocity_plots(df):
    """
    Makes plots showing game velocity for SAS and IND

    Args:
        df (pd.DataFrame): dataframe of velocity data
            Note: use extract_velocity() to obtain this data

    Returns:
        None
        Saves plots to examples/
    """

    # Organize velocity data
    home = df[[0, 2, 5, 7]]
    away = df[[1, 3, 4, 6]]
    home.columns = ['Off', 'Def', 'Pts', 'Tm']
    away.columns = ['Off', 'Def', 'Pts', 'Tm']
    all_dat = pd.concat((home, away))
    ave = all_dat.groupby('Tm').mean()

    # Plot of offense velocity by team
    plt.figure()
    sns.barplot(x='Tm', y='Off', data=all_dat,
                order=ave.sort_values('Off').index,
                color=sns.xkcd_rgb["pale red"])
    plt.ylim(0.022, 0.03)
    locs, labels = plt.xticks()
    plt.setp(labels, rotation=90)
    locs, labels = plt.yticks()
    plt.yticks(locs, map(lambda x: "%.1f" % x, locs*1000))
    plt.ylabel('Mean Offensive Velocity (ft/sec)')
    plt.xlabel('')
    plt.title('Offensive Velocity')
    plt.savefig('examples/VelocityOffenseTeams')

    # Plot of defense velocity by team
    plt.figure()
    sns.barplot(x='Tm', y='Def', data=all_dat,
                order=ave.sort_values('Def').index,
                color=sns.xkcd_rgb["pale red"])
    plt.ylim(0.018, 0.024)
    locs, labels = plt.xticks()
    plt.setp(labels, rotation=90)
    locs, labels = plt.yticks()
    plt.yticks(locs, map(lambda x: "%.1f" % x, locs*1000))
    plt.ylabel('Mean Defensive Velocity (ft/sec)')
    plt.xlabel('')
    plt.title('Defensive Velocity')
    plt.savefig('examples/VelocityDefenseTeams')


def fatigue_plots(df):
    """
    Makes plots showing game fatigue for SAS and IND

    Args:
        df (pd.DataFrame): dataframe of fatigue data
            Note: use extract_fatigue() to obtain this data

    Returns:
        None
        Saves plots to examples/
    """
    plt.figure()
    sns.swarmplot(x='variable', y='value',
                  data=df[df.Pos == 'Off'][df.Tm == 'IND'])
    plt.title('Indiana Pacers Fatigue')
    plt.xlabel('Quarter')
    plt.ylabel('Mean Offensive Velocity (ft/sec)')
    plt.ylim(0.015, 0.034)
    locs, labels = plt.yticks()
    plt.yticks(locs, map(lambda x: "%.1f" % x, locs*1000))
    plt.savefig('examples/INDfatige')

    plt.figure()
    sns.swarmplot(x='variable', y='value',
                  data=df[df.Pos == 'Off'][df.Tm == 'SAS'])
    plt.title('San Antonio Spurs Fatigue')
    plt.xlabel('Quarter')
    plt.ylabel('Mean Offensive Velocity (ft/sec)')
    locs, labels = plt.yticks()
    plt.yticks(locs, map(lambda x: "%.1f" % x, locs*1000))
    plt.savefig('examples/SASfatige')


def extract_scores(score_data):
    """
    Organizes score data from string to tuple

    Args:
        score_data (str): string of form 'AWAYSCORE - HOMESCORE'
            Example: '111 - 105'

    Returns:
        scores (tuple): tuple of form (away_score, home_score) where
            each score is an int
    """
    away_score = int(score_data.split('-')[0])
    home_score = int(score_data.split('-')[1])
    scores = (away_score, home_score)
    return scores


def set_plot_params(size):
    """
    Sets font size on plots.  16-22 is a good range.
    """
    SIZE = size
    plt.rc('font', size=SIZE)
    plt.rc('axes', titlesize=SIZE)
    plt.rc('axes', labelsize=SIZE)
    plt.rc('xtick', labelsize=SIZE)
    plt.rc('ytick', labelsize=SIZE)
    plt.rc('legend', fontsize=SIZE)


if __name__ == "__main__":
    set_plot_params(16)
    all_games = extract_games()
    write_velocity(all_games)
    velocity_data = extract_velocity(all_games)
    velocity_plots(velocity_data)
    fatigue_data = extract_fatigue(all_games)
    fatigue_plots(fatigue_data)
