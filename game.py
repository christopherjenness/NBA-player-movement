"""
Library for retrieving basektball player-tracking and play-by-play data.
"""

# brew install p7zip
# brew install curl
# brew install ffmpeg --with-libvpx

import os
import warnings
import json
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Arc, Polygon
import numpy as np
import seaborn as sns
from scipy.spatial import ConvexHull
from subprocess import Popen, PIPE

#Initialize Project
os.chdir('/Users/christopherjenness/Desktop/Personal/SportVU/NBA-player-movement')
os.system('mkdir temp')

class Game(object):
    """
    Class for basketball game.
    Contains play by play and player tracking data and methods for anaylsis and plotting.
    """

    def __init__(self, date, team1, team2):
        """
        Args:
            date (str): 'MM.DD.YYYY', date of game
            team1 (str): 'XXX', abbreviation of team1 in data tracking file name
            team2 (str): 'XXX', abbreviation of team2 in data tracking file name

        Attributes:
            date (str): 'MM.DD.YYYY', date of game
            team1 (str): 'XXX', abbreviation of team1 in data tracking file name
            team2 (str): 'XXX', abbreviation of team2 in data tracking file name
            tracking_id (str): id to access player tracking data
                Due to the way the SportVU data is stored, game_id is
                complicated: 'MM.DD.YYYY.AWAYTEAM.at.HOMETEAM'
                For Example: 01.13.2016.GSW.at.DEN
            tracking_data (dict): Dictionary of unstructured tracking data scraped from github.
            game_id (str): ID for game.  Lukcily, SportVU and play by play use the same game ID
            pbp (pd.DataFrame): Play by play data.  33 columns per pbp instance.
            moments (pd.DataFrame): DataFrame of player tracking data.  Each entry is a single
                snap-shot of where the players are at a given time on the court.
                Columns: ['quarter', 'universe_time', 'quarter_time', 'shot_clock',
                'positions', 'game_time'].
                moments['positions'] contains a list of where each player and the ball
                are located.
            player_ids (dict): dictionary of {player: player_id} for all players in game.
            away_id (int): ID of away team
            home_id (int): ID of home team
            team_colors (dict): dictionary of colors for each team and ball.  Used for ploting.
            home_team (str): 'XXX', abbreviation of home team
            away_team (str): 'XXX', abbreviation of away team
        """
        self.date = date
        self.team1 = team1
        self.team2 = team2
        self.flip_direction = False
        self.tracking_id = '{self.date}.{self.team2}.at.{self.team1}'.format(self=self)
        self.tracking_data = None
        self.game_id = None
        self.pbp = None
        self.moments = None
        self.player_ids = None
        self._get_tracking_data()
        self._get_playbyplay_data()
        self._format_tracking_data()
        self._get_player_ids()
        self.away_id = self.tracking_data['events'][0]['visitor']['teamid']
        self.home_id = self.tracking_data['events'][0]['home']['teamid']
        self.team_colors = {-1: "orange",
                            self.away_id: "blue",
                            self.home_id: "red"}
        self.home_team = self.tracking_data['events'][0]['home']['abbreviation']
        self.away_team = self.tracking_data['events'][0]['visitor']['abbreviation']
        self.flip_direction = False
        self._determine_direction()
        print('All data is loaded')

    def _get_tracking_data(self):
        """
        Helper function for retrieving tracking data
        Tracking Data is provided by NBA.com, hosted at: https://www.github.com/neilmj
        """
        # Retrive and extract Data into /temp folder

        datalink = ("https://raw.githubusercontent.com/1wheel/BasketballData/master/"
                    "2016.NBA.Raw.SportVU.Game.Logs/{self.tracking_id}.7z").format(self=self)
        print(datalink)
        os.system("curl {datalink} -o temp/zipdata".format(datalink=datalink))
        os.system("7za -o./temp x temp/zipdata")
        os.remove("./temp/zipdata")

        # Extract game ID from extracted file name.
        for file in os.listdir('./temp'):
            if os.path.splitext(file)[1] == '.json':
                self.game_id = file[:-5]

        # Load tracking data and remove json file
        with open('temp/{self.game_id}.json'.format(self=self)) as data_file:
            self.tracking_data = json.load(data_file) # Load this json
        os.remove('./temp/{self.game_id}.json'.format(self=self))
        return self

    def _get_playbyplay_data(self):
        """
        Helper function for retrieving play-by-play data.
        Play-by-play data is obtained via API call to NBA.com
        This service is likely to go down at any moment and ruin this whole project.
        """
        # stats.nba.com API call
        os.system('curl "http://stats.nba.com/stats/playbyplayv2?'
                  'EndPeriod=0&'
                  'EndRange=0&'
                  'GameID={self.game_id}&'
                  'RangeType=0&'
                  'Season=2015-16&'
                  'SeasonType=Season&'
                  'StartPeriod=0&'
                  'StartRange=0" > {cwd}/temp/pbp_{self.game_id}.json'.format(cwd=os.getcwd(), self=self))

        # load play by play into pandas DataFrame
        with open("{cwd}/temp/pbp_{self.game_id}.json".format(cwd=os.getcwd(), self=self)) as json_file:
            parsed = json.load(json_file)['resultSets'][0]
        os.remove("{cwd}/temp/pbp_{self.game_id}.json".format(cwd=os.getcwd(), self=self))
        self.pbp = pd.DataFrame(parsed['rowSet'])
        self.pbp.columns = parsed['headers']

        # Get time in quarter reamining to cross-reference tracking data
        self.pbp['Qmin'] = self.pbp['PCTIMESTRING'].str.split(':', expand=True)[0]
        self.pbp['Qsec'] = self.pbp['PCTIMESTRING'].str.split(':', expand=True)[1]
        self.pbp['Qtime'] = self.pbp['Qmin'].astype(int)*60 + self.pbp['Qsec'].astype(int)
        self.pbp['game_time'] = (self.pbp['PERIOD'] - 1) * 720 + (720 - self.pbp['Qtime'])

        #Format score so that it makes sense: 'XX-XX'
        self.pbp['SCORE'] = self.pbp['SCORE'].fillna(method='ffill').fillna('0 - 0')
        return self

    def _get_player_ids(self):
        """
        Helper function for returning player ids for all players in game.
        Note: This data may also be somewhere more conveniently accessible in tracking_data.
        """
        ids = {}
        for index, row in self.pbp.iterrows():
            if row['PLAYER1_NAME'] not in ids:
                ids[row['PLAYER1_NAME']] = row['PLAYER1_ID']
            if row['PLAYER2_NAME'] not in ids:
                ids[row['PLAYER2_NAME']] = row['PLAYER2_ID']
            if row['PLAYER3_NAME'] not in ids:
                ids[row['PLAYER3_NAME']] = row['PLAYER3_ID']
        ids.pop(None)
        self.player_ids = ids
        return self

    def _format_tracking_data(self):
        """
        Heler function to format tracking data into pandas DataFrame
        """
        events = pd.DataFrame(self.tracking_data['events'])
        moments = []
        # Extract 'moments': Each moment is an individual frame from the tracking cameras
        for row in events['moments']:
            for inner_row in row:
                moments.append(inner_row)
        moments = pd.DataFrame(moments)
        moments = moments.drop_duplicates(subset=[1])
        moments = moments.reset_index()

        moments.columns = ['index', 'quarter', 'universe_time', 'quarter_time',
                           'shot_clock', 'unknown', 'positions']
        moments['game_time'] = (moments.quarter - 1) * 720 + (720 - moments.quarter_time)
        moments.drop(['index', 'unknown'], axis=1, inplace=True)
        self.moments = moments
        return self

    def _draw_court(self, color="gray", lw=2, grid=False, zorder=0):
        """
        Helper function to draw court.
        Modified from Savvas Tjortjoglou with contribution from Michael Wheelock
        Savvas Tjortjoglou: http://savvastjortjoglou.com/nba-shot-sharts.html
        Michael Wheelock: https://www.linkedin.com/in/michael-s-wheelock-a5635a66
        """
        ax = plt.gca()

        # Create the court lines
        outer = Rectangle((0, -50), width=94, height=50, color=color, zorder=zorder, fill=False, lw=lw)
        l_hoop = Circle((5.35, -25), radius=.75, lw=lw, fill=False, color=color, zorder=zorder)
        r_hoop = Circle((88.65, -25), radius=.75, lw=lw, fill=False,color=color, zorder=zorder)
        l_backboard = Rectangle((4, -28), 0, 6, lw=lw, color=color, zorder=zorder)
        r_backboard = Rectangle((90, -28), 0, 6, lw=lw, color=color, zorder=zorder)
        l_outer_box = Rectangle((0, -33), 19, 16, lw=lw, fill=False, color=color, zorder=zorder)
        l_inner_box = Rectangle((0, -31), 19, 12, lw=lw, fill=False, color=color, zorder=zorder)
        r_outer_box = Rectangle((75, -33), 19, 16, lw=lw, fill=False, color=color, zorder=zorder)
        r_inner_box = Rectangle((75, -31), 19, 12, lw=lw, fill=False, color=color, zorder=zorder)
        l_free_throw = Circle((19, -25), radius=6, lw=lw, fill=False, color=color, zorder=zorder)
        r_free_throw = Circle((75, -25), radius=6, lw=lw, fill=False, color=color, zorder=zorder)
        l_corner_a = Rectangle((0, -3), 14, 0, lw=lw, color=color, zorder=zorder)
        l_corner_b = Rectangle((0, -47), 14, 0, lw=lw, color=color, zorder=zorder)
        r_corner_a = Rectangle((80, -3), 14, 0, lw=lw, color=color, zorder=zorder)
        r_corner_b = Rectangle((80, -47), 14, 0, lw=lw, color=color, zorder=zorder)
        l_arc = Arc((5, -25), 47.5, 47.5, theta1=292, theta2=68, lw=lw, color=color, zorder=zorder)
        r_arc = Arc((89, -25), 47.5, 47.5, theta1=112, theta2=248, lw=lw, color=color, zorder=zorder)
        half_court = Rectangle((47, -50), 0, 50, lw=lw, color=color, zorder=zorder)
        hc_big_circle = Circle((47, -25), radius=6, lw=lw, fill=False, color=color, zorder=zorder)
        hc_sm_circle = Circle((47, -25), radius=2, lw=lw, fill=False, color=color, zorder=zorder)
        court_elements = [l_hoop, l_backboard, l_outer_box, outer,
                          l_inner_box, l_free_throw, l_corner_a,
                          l_corner_b, l_arc, r_hoop, r_backboard,
                          r_outer_box, r_inner_box, r_free_throw,
                          r_corner_a, r_corner_b, r_arc, half_court,
                          hc_big_circle, hc_sm_circle]

        # Add the court elements onto the axes
        for element in court_elements:
            ax.add_patch(element)

        return ax

    def watch_play(self, game_time, length, highlight_player=None, commentary=True, show_spacing=None):
        """
        DEPRECIATED.  See animate_play() for similar (fastere) method

        Method for viewing plays in game.
        Outputs video file of play in {cwd}/temp

        Args:
            game_time (int): time in game to start video (seconds into the game).
                Currently game_time can also be an tuple of length two with (starting_frame, ending_frame)
                if you want to watch a play using frames instead of game time.
            length (int): length of play to watch (seconds)
            highlight_player (str): If not None, video will highlight the circle of
                the inputed player for easy tracking.
            commentary (bool): Whether to include play-by-play commentary underneath video
            show_spacing (str in ['home', 'away']): show convex hull of home or away team
                if None, does not display any convex hull

        Returns: an instance of self, and outputs video file of play
        """
        warnings.warn("watch_play is extremely slow.  Use animate_play for similar functionality, but greater efficiency")
        
        if type(game_time) == tuple:
            starting_frame = game_time[0]
            ending_frame = game_time[1]
        else:
            # Get starting and ending frame from requested game_time and length
            starting_frame = self.moments[self.moments.game_time.round() == game_time].index.values[0]
            ending_frame = self.moments[self.moments.game_time.round() == game_time + length].index.values[0]

        # Make video of each frame
        for frame in range(starting_frame, ending_frame):
            self.plot_frame(frame, highlight_player=highlight_player, 
                            commentary=commentary, show_spacing=show_spacing)
        command = 'ffmpeg -framerate 20 -start_number {starting_frame} -i %d.png -c:v libx264 -r 30 -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" {starting_frame}.mp4'.format(starting_frame=starting_frame)
        os.chdir('temp')
        os.system(command)
        os.chdir('..')

        #Delete images
        for file in os.listdir('./temp'):
            if os.path.splitext(file)[1] == '.png':
                os.remove('./temp/{file}'.format(file=file))

        return self

    def watch_player_actions(self, player_name, action, length=15, max_vids=5):
        """
        Method for viewing all plays a player in the game had of a specified type.
        For example: all of Damian Lillards FG attempts in the game
        Outputs video file for each play in {cwd}/temp

        Args:
            player_name (str): Name of player for which to produce videos.
                Currently, player_name must be perfectly formatted and capitalized, since
                no string processing is performed.
            action {'all_FG', 'made_FG', 'miss_FG', 'rebound'}: Action type of interest
            length (int): length of play to watch (seconds) for each action.
            max_vids (int): Maximum number of videos to produce.  max_vids=None if all videos are
                desired.  If max_vids is less than the total number of actions in the game, the
                earliest actions are made into videos.

        Returns: an instance of self, and outputs video file of plays
        """
        player_action_times = self._get_player_actions(player_name, action)
        for index, time in enumerate(player_action_times):
            if index == max_vids:
                break
            self.watch_play(time-length, length, highlight_player=player_name, commentary=False)
        return self

    def _get_commentary(self, game_time, commentary_length=6, commentary_depth=10):
        """
        Helper function for returning play by play events for a given game time.

        Args:
            game_time (int): game time (in seconds) for which to retrieve commentary for
            commentary_length (int): Number of play-by-play calls to include in commentary
            commentary_depth (int): Number of seconds to look in past to retrieve play-by-play calls
                commentary_depth=10 looks at previous 10 seconds of game for play-by-play calls

        Returns: tuple of information (commentary_script, score)
            commentary_script (str): string of commentary
                Most recent play-by-play calls, seperated by line breaks
            score (str): Score at current time 'XX - XX'
        """
        commentary = [' 'for i in range(commentary_length)]
        commentary[0] = '.'
        count = 0
        score = "0 - 0"
        for game_second in range(game_time - commentary_depth, game_time + 2):
            for index, row in self.pbp[self.pbp.game_time == game_second].iterrows():
                if row['HOMEDESCRIPTION']:
                    commentary[count] = '{self.home_team}: '.format(self=self) + str(row['HOMEDESCRIPTION'])
                    count += 1
                if row['VISITORDESCRIPTION']:
                    commentary[count] = '{self.away_team}: '.format(self=self) + str(row['VISITORDESCRIPTION'])
                    count += 1
                if row['NEUTRALDESCRIPTION']:
                    commentary[count] = str(row['NEUTRALDESCRIPTION'])
                    count += 1
                score = str(row['SCORE'])
                if count == commentary_length - 1:
                    break
        commentary_script = """{commentary[0]}
                                \n{commentary[1]} 
                                \n{commentary[2]} 
                                \n{commentary[3]} 
                                \n{commentary[4]} 
                                \n{commentary[5]}
                                """.format(commentary=commentary)
        return (commentary_script, score)

    def _get_player_actions(self, player_name, action):
        """
        Helper function to get all times a player performed a specific action
        
        Args:
            player_name (str): name of player to get all actions for
            action {'all_FG', 'made_FG', 'miss_FG', 'rebound'}: Type of action to get all times for.
            
        Returns:
            times (list): list of game times a player performed a specific specific action
        """
        player_id = self.player_ids[player_name]
        action_dict = {'all_FG': [1, 2], 'made_FG': [1], 'miss_FG': [2], 'rebound': [4]}
        action_df = self.pbp[(self.pbp['PLAYER1_ID'] == player_id) & (self.pbp['EVENTMSGTYPE'].isin(action_dict[action]))]
        times = list(action_df['game_time'])
        return times

    def _get_moment_details(self, frame_number, highlight_player=None):
        """
        Helper function for getting important information for a given frame

        Args:
            frame_number (int): Frame in game to retrieve data for
                frame_number gets player tracking data from moments.ix[frame_number]
            highlight_player (str): Name of player to be highlighted in downstream plotting.
                if None, no player is highlighted.

        Returns: tuple of data
            game_time (int): seconds into game of current moment
            x_pos (list): list of x coordinants for all players and ball
            y_pos (list): list of y coordinants for all players and ball
            colors (list): color coding of each player/ball for coordinant data
            sizes (list): size of each player/ball (used for showing ball height)
            quarter (int): Game quarter
            shot_clock (str): shot clock
            game_clock (str): game clock
            edges (list): list of marker edge sizes of each player for video.
                useful when trying to highlight a player by making their edge thicker.
            universe_time (int): Time in the universe, in msec
        """
        current_moment = self.moments.ix[frame_number]
        game_time = int(np.round(current_moment['game_time']))
        universe_time = int(current_moment['universe_time'])
        x_pos, y_pos, colors, sizes, edges = [], [], [], [], []
        # Get player positions
        for player in current_moment.positions:
            x_pos.append(player[2])
            y_pos.append(player[3])
            colors.append(self.team_colors[player[0]])
            # Use ball height for size (useful to sevie a shot)
            if player[0] == -1:
                sizes.append(max(150 - 2*(player[4] - 5)**2, 10))
            else:
                sizes.append(200)
            # highlight_player makes their outline much thicker on the video
            if highlight_player and player[1] == self.player_ids[highlight_player]:
                edges.append(5)
            else:
                edges.append(0.5)
        # Unfortunately, the plot is below the y axis, so the y positions need to be corrected
        y_pos = np.array(y_pos) - 50
        shot_clock = current_moment.shot_clock
        if np.isnan(shot_clock):
            shot_clock = 24.00
        shot_clock = str(shot_clock).split('.')[0]
        game_min, game_sec = divmod(current_moment.quarter_time, 60)
        game_clock = "%02d:%02d" % (game_min, game_sec)
        quarter = current_moment.quarter
        return (game_time, x_pos, y_pos, colors, sizes, quarter, shot_clock, game_clock, edges, universe_time)

    def plot_frame(self, frame_number, highlight_player=None,
                   commentary=True, show_spacing=False,
                   plot_spacing=False, pipe=None):
        """
        Creates an individual the frame of game.
        Outputs .png file in {cwd}/temp

        Args:
            frame_number (int): number of frame in game to create
                frame_number gets player tracking data from moments.ix[frame_number]
            highlight_player (str): Name of player to highlight (by making their outline thicker).
                if None, no player is highlighted
            commentary (bool): if True, add play-by-play commentary under frame
            show_spacing (str in ['home', 'away']): show convex hull of home or away team
                if None, does not display any convex hull
            pipe (subprocesses.Popen): Popen object with open pipe to send image to
                if False, image is written to disk instead of sent to pipe

        Returns: an instance of self, and outputs .png file of frame
            If pipe, ARGB values are sent to pipe object instead of writing to disk.

        TODO be able to call this method by game time instead of frame_number
        """
        (game_time, x_pos, y_pos, colors, sizes, quarter, shot_clock, game_clock, edges, universe_time) = self._get_moment_details(frame_number, highlight_player=highlight_player)
        (commentary_script, score) = self._get_commentary(game_time)
        fig = plt.figure(figsize=(12, 6))
        self._draw_court()
        frame = plt.gca()
        frame.axes.get_xaxis().set_ticks([])
        frame.axes.get_yaxis().set_ticks([])
        plt.scatter(x_pos, y_pos, c=colors, s=sizes, alpha=0.85, linewidths=edges)
        plt.xlim(-5, 100)
        plt.ylim(-55, 5)
        sns.set_style('dark')
        if commentary:
            plt.figtext(0.23, -.6, commentary_script, size=20)
        plt.figtext(0.43, 0.125, shot_clock, size=18)
        plt.figtext(0.5, 0.125, 'Q'+str(quarter), size=18)
        plt.figtext(0.57, 0.125, str(game_clock), size=18)
        plt.figtext(0.43, .85, self.away_team + "  " + score + "  " + self.home_team, size=18)
        if highlight_player:
            plt.figtext(0.17, 0.85, highlight_player, size=18)
        # Add team color indicators to top of frame
        plt.scatter([30, 67], [2.5, 2.5], s=100,
                    c=[self.team_colors[self.away_id], self.team_colors[self.home_id]])
        if show_spacing:
            # Show convex hull on frame
            xy_pos = np.column_stack((np.array(x_pos), np.array(y_pos)))
            if show_spacing == 'home':
                points = xy_pos[1:6, :]
            if show_spacing == 'away':
                points = xy_pos[6:, :]
            hull = ConvexHull(points)
            hull_points = points[hull.vertices, :]
            polygon = Polygon(hull_points, alpha=0.3, color='gray')
            ax=plt.gca()
            ax.add_patch(polygon)
        if pipe:
            # Write ARGB values to pipe
            fig.canvas.draw()
            string = fig.canvas.tostring_argb()
            pipe.stdin.write(string)
            plt.close()
            if commentary: 
                fig = plt.figure(figsize=(12, 6))
                plt.figtext(.2, .4, commentary_script, size=20)
                fig.canvas.draw()
                string = fig.canvas.tostring_argb()
                pipe.stdin.write(string)
            plt.close()

        else:
            # Save image to disk
            plt.savefig('temp/{frame_number}.png'.format(frame_number=frame_number), bbox_inches='tight')
            plt.close()
        return self
        
    def _in_formation(self, frame_number):
        """
        This is a complicated method to explain, but it is actually very simple.
        It determines if the game is in a set offense/defense.
        It basically returns True if a normal play is being run, and False if the
        game is in transition, out of bounds, free throw, etc.  It is useful for
        analyzing plays that teams run, and discarding all extranous times from the game.
        """
        # Get relevant moment details
        details = self._get_moment_details(frame_number)
        x_pos = np.array(details[1])
        shot_clock = details[6]
        # Determine if offense/defense is set
        if float(shot_clock) < 23:
            if (x_pos < 47).all() or (x_pos > 47).all():
                return True
        return False

    def get_spacing_area(self, frame_number):
        """
        Calculates convex hull of home and away team for a given frame.
        Useful for analyzing the spacing of teams.

        Args:
            frame_number (int): number of frame in game to calculate team convex hulls

        Returns: tuple of data (home_area, away_area)
            home_area (float): convex hull area of home team
            away_area (float): convex hull area of away team

        """
        details = self._get_moment_details(frame_number)
        x_pos = np.array(details[1])
        y_pos = np.array(details[2])
        xy_pos = np.column_stack((x_pos, y_pos))
        home_area = ConvexHull(xy_pos[1:6, :]).area
        away_area = ConvexHull(xy_pos[6:, :]).area
        return (home_area, away_area)

    def get_offensive_team(self, frame_number):
        """
        Determines which team is on offense.
        Currently only works if team is in set offense or defense.

        Args:
            frame_number (int): number of frame in game to determine offensive team

        Returns:
            str in ['home', 'away']
        """
        details = self._get_moment_details(frame_number)
        x_pos = np.array(details[1])
        shot_clock = int(details[6])
        quarter = details[5]
        if len(x_pos) != 11:
            return None
        if self.flip_direction:
            if (x_pos < 47).all() and quarter in [1, 2]:
                return 'away'
            if (x_pos > 47).all() and quarter in [3, 4]:
                return 'away'
            if (x_pos < 47).all() and quarter in [3, 4]:
                return 'home'
            if (x_pos > 47).all() and quarter in [1, 2]:
                return 'home'
        if (x_pos < 47).all() and quarter in [1, 2]:
            return 'home'
        if (x_pos > 47).all() and quarter in [3, 4]:
            return 'home'
        if (x_pos < 47).all() and quarter in [3, 4]:
            return 'away'
        if (x_pos > 47).all() and quarter in [1, 2]:
            return 'away'
        return None

    def _determine_direction(self):
        """
        Helper funcation to determine which direction the home team is going.
        Surprisingly, this is not consistent and depends on the game.
        Currently, this method detects which side the players start on and is
        ~90% accurate
        """
        incorrect_count = 0
        correct_count = 0
        for frame in range(0, 10000, 100):
            details=self._get_moment_details(frame)
            home_team_x = details[1][1:6]
            away_team_x = details[1][6:]
            if np.mean(home_team_x) < np.mean(away_team_x):
                incorrect_count += 1
            else:
                correct_count += 1
        if incorrect_count > correct_count:
            self.flip_direction = True
        return None
    
    def get_frame(self, game_time):
        """
        Converts a game time to a frame number.  Useful all over the place.f
        
        Args:
            game_time (int): game time in seconds of interest
            
        Returns: 
            frame (int): frame number of game time
        """
        test_time = game_time
        while True: 
            if test_time in self.moments.game_time.round():
                frames = self.moments[self.moments.game_time.round() == test_time].index.values
                if len(frames) > 0:
                    frame = frames[0]
                    break
                else:
                    test_time -= 1
            else:
                test_time -= 1
        return frame
        
    def get_play_frames(self, event_num, play_type='offense'):
        """
        Args:
            event_num (int): EVENTNUM of interest in games.pbp
                NOTE: Check pbpevents.txt for event numbers
            play_type (str in ['offense', 'defense']): Team of interest is offense or defense
        
        Returns:
            tuple of (start_time (int), end_time (int)): start time and end time in seconds 
                for play of interest
        """
        play_index = self.pbp[self.pbp['EVENTNUM']==event_num].index[0]
        event_team = str(self.pbp[self.pbp['EVENTNUM'] == event_num].PLAYER1_TEAM_ABBREVIATION.head(1).values[0])
        if event_team == self.home_team:
            target_team = 'home'
        if event_team == self.away_team:
            target_team = 'away'
        end_time = int(self.pbp[self.pbp['EVENTNUM'] == event_num].game_time)
        #find lower bound on starting frame of the play by determining when previous play ended
        putative_start_time = int(self.pbp.ix[play_index-1].game_time)
        putative_start_frame = self.get_frame(putative_start_time)
        end_frame = self.get_frame(end_time)
        for test_frame in range(putative_start_frame, end_frame):
            if self.get_offensive_team(test_frame) == target_team:
                break
        # if the previous loop never found an offensive play, the function returns None
        else:
            return None
        # Add two seconds to game time to let the players settle into position
        start_frame = self.get_frame(round(self.moments.ix[test_frame].game_time + 2))
        return (start_frame, end_frame)
        
    def animate_play(self, game_time, length, highlight_player=None, commentary=True, show_spacing=None):
        """
        Method for animating plays in game.
        Outputs video file of play in {cwd}/temp.
        Individual frames are streamed directly to ffmpeg without writing them
        to the disk, which is a great speed improvement over watch_play

        Args:
            game_time (int): time in game to start video (seconds into the game).
                Currently game_time can also be an tuple of length two with (starting_frame, ending_frame)
                if you want to watch a play using frames instead of game time.
            length (int): length of play to watch (seconds)
            highlight_player (str): If not None, video will highlight the circle of
                the inputed player for easy tracking.
            commentary (bool): Whether to include play-by-play commentary in 
                the animation
            show_spacing (str) in ['home', 'away']: show convex hull spacing of home or away
                team.  If None, does not show spacing.

        Returns: an instance of self, and outputs video file of play
        """
        if type(game_time) == tuple:
            starting_frame = game_time[0]
            ending_frame = game_time[1]
        else:
            # Get starting and ending frame from requested game_time and length
            starting_frame = self.moments[self.moments.game_time.round() == game_time].index.values[0]
            ending_frame = self.moments[self.moments.game_time.round() == game_time + length].index.values[0]

        # Make video of each frame
        filename = "./temp/{game_time}.mp4".format(game_time=game_time)
        if commentary:
            size = (960, 960)
        else:
            size = (960, 480)
        cmdstring = ('ffmpeg', 
            '-y', '-r', '20', # 0fps
            '-s', '%dx%d' % size, # size of image string
            '-pix_fmt', 'argb', # Stream argb data from matplotlib
            '-f', 'rawvideo',  '-i', '-',
            '-vcodec', 'libx264', filename) 
        
        #Stream plots to pipe
        pipe = Popen(cmdstring, stdin=PIPE)
        for frame in range(starting_frame, ending_frame):
            self.plot_frame(frame, highlight_player=highlight_player, 
                            commentary=commentary, show_spacing=show_spacing, 
                            pipe=pipe)
        pipe.stdin.close()
        pipe.wait()
        return self
