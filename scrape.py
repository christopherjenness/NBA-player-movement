"""
Library for retrieving basektball player-tracking and play-by-play data.
"""

# brew install p7zip

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Arc
import numpy as np
import seaborn as sns

os.chdir('/Users/christopherjenness/Desktop/Personal/SportVU/NBA-player-movement')
os.system('mkdir temp')

class Game(object):
    """
    Class for basketball game.  Retrieves play by play and player tracking data.
    """
    
    def __init__(self, date, home_team, away_team):
        """
        Args:
            date (str): 'MM.DD.YYYY', date of game
            home_team (str): 'XXX', abbreviation of home team
            away_team (str): 'XXX', abbreviation of away team
        
        Attributes:
            date (str): 'MM.DD.YYYY', date of game
            home_team (str): 'XXX', abbreviation of home team
            away_team (str): 'XXX', abbreviation of away team
            tracking_id (str): id to access player tracking data
                Due to the way the SportVU data is stored, game_id is 
                complicated: 'MM.DD.YYYY.AWAYTEAM.at.HOMETEAM'
                For Example: 01.13.2016.GSW.at.DEN
            pbp (pd.DataFrame): Play by play data.  33 columns per pbp instance.
            game_id (str): ID for game.  Lukcily, SportVU and play by play use the same game ID
        """
        self.date = date
        self.home_team = home_team
        self.away_team = away_team
        self.tracking_id = '{self.date}.{self.away_team}.at.{self.home_team}'.format(self=self)
        self.tracking_data = None
        self.game_id = None
        self.pbp = None
        self.moments = None
        self._get_tracking_data()
        self._get_playbyplay_data()
        self._format_tracking_data()
        self.team_colors = {-1: "orange",
                      self.moments.ix[0].positions[1][0]: "blue",
                      self.moments.ix[0].positions[6][0]: "red"}
        print('done loading data')
    
    def _get_tracking_data(self):
        """
        Helper function for retrieving tracking data
        """
        # Extract Data into /temp folder
        datalink = "https://raw.githubusercontent.com/neilmj/BasketballData/master/2016.NBA.Raw.SportVU.Game.Logs/{self.tracking_id}.7z".format(self=self)
        os.system("curl " + datalink + " -o " + os.getcwd() + '/temp/zipdata') 
        os.system("7za -o./temp x " + os.getcwd() + '/temp/zipdata') 
        os.remove("./temp/zipdata")
        
        # Extract game ID from extracted file name.
        for file in os.listdir('./temp'):
            if file.endswith('.json'):
                self.game_id = file[:-5]
        
        # Load tracking data
        with open('temp/{self.game_id}.json'.format(self=self)) as data_file:
            self.tracking_data = json.load(data_file) # Load this json
        os.remove('./temp/{self.game_id}.json'.format(self=self))
        return self

    def _get_playbyplay_data(self):
        """
        Helper function for retrieving tracking data
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
        self.pbp.columns= parsed['headers']
        
        # Get time in quarter reamining to cross-reference tracking data
        self.pbp.Qmin = self.pbp.PCTIMESTRING.str.split(':', expand=True)[0]
        self.pbp.Qsec = self.pbp.PCTIMESTRING.str.split(':', expand=True)[1]
        self.pbp.Qtime = self.pbp.Qmin.astype(int)*60 + self.pbp.Qsec.astype(int)
        self.pbp.game_time = (self.pbp.PERIOD - 1) * 720 + (720 - self.pbp.Qtime)
        return self
        
    def _format_tracking_data(self):
        """
        Heler function to format tracking data into pandas DataFrame
        """
        events = pd.DataFrame(self.tracking_data['events'])
        moments=[]
        # Extract 'moments' 
        for row in events['moments']:
            for inner_row in row:
                moments.append(inner_row)
        moments = pd.DataFrame(moments)
        moments = moments.drop_duplicates(subset=[1])
        moments = moments.reset_index()
        moments.columns = ['index', 'quarter', 'universe_time', 'quarter_time', 'shot_clock', 'unknown', 'positions']
        moments['game_time'] = (moments.quarter - 1) * 720 + (720 - moments.quarter_time)
        self.moments = moments

    def _draw_court(self, color="gray", lw=2, grid=False, zorder=0):
        """
        Helper function to draw court.
        Modified from Savvas Tjortjoglou
        http://savvastjortjoglou.com/nba-shot-sharts.html
        """
        ax = plt.gca()
        # Creates the out of bounds lines around the court
        outer = Rectangle((0,-50), width=94, height=50, color=color,
                      zorder=zorder, fill=False, lw=lw)

        # The left and right basketball hoops
        l_hoop = Circle((5.35,-25), radius=.75, lw=lw, fill=False, color=color, zorder=zorder)
        r_hoop = Circle((88.65,-25), radius=.75, lw=lw, fill=False,color=color, zorder=zorder)
        
        # Left and right backboards
        l_backboard = Rectangle((4,-28), 0, 6, lw=lw, color=color, zorder=zorder)
        r_backboard = Rectangle((90, -28), 0, 6, lw=lw, color=color, zorder=zorder)

        # Left and right paint areas
        l_outer_box = Rectangle((0, -33), 19, 16, lw=lw, fill=False,
                                color=color, zorder=zorder)    
        l_inner_box = Rectangle((0, -31), 19, 12, lw=lw, fill=False,
                                color=color, zorder=zorder)
        r_outer_box = Rectangle((75, -33), 19, 16, lw=lw, fill=False,
                                color=color, zorder=zorder)

        r_inner_box = Rectangle((75, -31), 19, 12, lw=lw, fill=False,
                                color=color, zorder=zorder)

        # Left and right free throw circles
        l_free_throw = Circle((19,-25), radius=6, lw=lw, fill=False,
                              color=color, zorder=zorder)
        r_free_throw = Circle((75, -25), radius=6, lw=lw, fill=False,
                              color=color, zorder=zorder)

        # Left and right corner 3-PT lines
        # a is top lines
        # b is the bottom lines
        l_corner_a = Rectangle((0,-3), 14, 0, lw=lw, color=color,
                               zorder=zorder)
        l_corner_b = Rectangle((0,-47), 14, 0, lw=lw, color=color,
                               zorder=zorder)
        r_corner_a = Rectangle((80, -3), 14, 0, lw=lw, color=color,
                               zorder=zorder)
        r_corner_b = Rectangle((80, -47), 14, 0, lw=lw, color=color,
                               zorder=zorder)
        
        # Left and right 3-PT line arcs
        l_arc = Arc((5,-25), 47.5, 47.5, theta1=292, theta2=68, lw=lw,
                    color=color, zorder=zorder)
        r_arc = Arc((89, -25), 47.5, 47.5, theta1=112, theta2=248, lw=lw,
                    color=color, zorder=zorder)

        # half_court
        # ax.axvline(470)
        half_court = Rectangle((47,-50), 0, 50, lw=lw, color=color,
                               zorder=zorder)
        hc_big_circle = Circle((47, -25), radius=6, lw=lw, fill=False,
                               color=color, zorder=zorder)
        hc_sm_circle = Circle((47, -25), radius=2, lw=lw, fill=False,
                              color=color, zorder=zorder)
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

    def watch_play(self, game_time, length):
        """
        Method for viewing plays in game.  Outputs video file of play in cwd
        
        Args:
            game_time: time in game to START play at
            length (int): length of play to watch in SECONDS
            
        Returns: an instance of self (and outputs video vile of play)
        """
        # Get starting and ending frame from requested game_time and length
        starting_frame = self.moments[self.moments.game_time.round() == game_time].index.values[0]
        ending_frame = self.moments[self.moments.game_time.round() == game_time + length].index.values[0]
        
        for frame in range(starting_frame, ending_frame):
            self.plot_frame(frame)
        command = 'ffmpeg -framerate 20 -start_number {starting_frame} -i %d.png -c:v libx264 -r 30 -pix_fmt yuv420p out.mp4'.format(starting_frame=starting_frame)
        os.chdir('temp')
        os.system(command) 
        os.chdir('..')
        
        #Delete images
        for file in os.listdir('./temp'):
            if file.endswith('.png'):
                os.remove('./temp/{file}'.format(file=file))

        return self
        
    def plot_frame(self, frame_number):
        """
        """
        game_time = int(np.round(self.moments.ix[frame_number]['game_time']))
        plt.figure(figsize=(12,6))
        #plt.figure()
        self._draw_court()
        x_pos = []
        y_pos = []
        colors = []
        sizes = []
        # Get player positions
        for player in self.moments.ix[frame_number].positions:
            x_pos.append(player[2])
            y_pos.append(player[3])
            colors.append(self.team_colors[player[0]])
            # Use ball height for size (useful to see a shot)
            if player[0]==-1:
                sizes.append(max(150 - 2*(player[4]-5)**2, 10))
            else:
                sizes.append(200)
        # Get recent play by play moves (from 10 previous seconds)
        commentary = ['.', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ']
        count = 0
        for game_second in range(game_time - 10, game_time + 2):
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
        commentary_script = """{commentary[0]}
                                \n{commentary[1]} 
                                \n{commentary[2]} 
                                \n{commentary[3]} 
                                \n{commentary[4]} 
                                \n{commentary[5]}
                                """.format(commentary=commentary)
        y_pos = np.array(y_pos)
        y_pos -= 50
        plt.scatter(x_pos, y_pos, c=colors, s=sizes)
        plt.xlim(-5, 100)
        plt.ylim(-55, 5)
        plt.figtext(0.23, -.6, commentary_script, size=20)
        #plt.title(commentary_script, size=20)
        plt.savefig('temp/{frame_number}.png'.format(frame_number=frame_number),bbox_inches='tight')
        plt.close()
        return self
        
a = Game('01.03.2016', 'DEN', 'POR') 



#a.watch_play(10, 60)

#a.watch_play(game_time=0,   length=2)



class loaded(object):
    def __init__(self, moments, pbp, home_team, away_team):
        self.moments = moments
        self.pbp = pbp
        self.team_colors = {-1: "orange",
                      self.moments.ix[0].positions[1][0]: sns.xkcd_rgb["denim blue"],
                      self.moments.ix[0].positions[6][0]: sns.xkcd_rgb["pale red"]}
        self.home_team = home_team
        self.away_team = away_team

    def plot_frame(self, frame_number):
        """
        """
        game_time = int(np.round(self.moments.ix[frame_number]['game_time']))
        fig = plt.figure(figsize=(12,6))
        #plt.figure()
        self._draw_court()
        x_pos = []
        y_pos = []
        colors = []
        sizes = []
        # Get player positions
        for player in self.moments.ix[frame_number].positions:
            x_pos.append(player[2])
            y_pos.append(player[3])
            colors.append(self.team_colors[player[0]])
            # Use ball height for size (useful to see a shot)
            if player[0]==-1:
                sizes.append(max(150 - 2*(player[4]-5)**2, 10))
            else:
                sizes.append(200)
        # Get recent play by play moves (from 10 previous seconds)
        commentary = ['.', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ']
        count = 0
        for game_second in range(game_time - 10, game_time + 2):
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
        commentary_script = """{commentary[0]}
                                \n{commentary[1]} 
                                \n{commentary[2]} 
                                \n{commentary[3]} 
                                \n{commentary[4]} 
                                \n{commentary[5]}
                                """.format(commentary=commentary)
        y_pos = np.array(y_pos)
        frame = plt.gca()
        frame.axes.get_xaxis().set_ticks([])
        frame.axes.get_yaxis().set_ticks([])
        y_pos -= 50
        plt.scatter(x_pos, y_pos, c=colors, s=sizes, alpha=0.85)
        plt.xlim(-5, 100)
        plt.ylim(-55, 5)
        sns.set_style('dark')
        plt.figtext(0.23, -.6, commentary_script, size=20)
        #plt.title(commentary_script, size=20)
        plt.savefig('temp/{frame_number}.png'.format(frame_number=frame_number),bbox_inches='tight')
        plt.show()
        plt.close()
        return self
    def _draw_court(self, color="gray", lw=2, grid=False, zorder=0):
        """
        Helper function to draw court.
        Modified from Savvas Tjortjoglou
        http://savvastjortjoglou.com/nba-shot-sharts.html
        """
        ax = plt.gca()
        # Creates the out of bounds lines around the court
        outer = Rectangle((0,-50), width=94, height=50, color=color,
                      zorder=zorder, fill=False, lw=lw)

        # The left and right basketball hoops
        l_hoop = Circle((5.35,-25), radius=.75, lw=lw, fill=False, color=color, zorder=zorder)
        r_hoop = Circle((88.65,-25), radius=.75, lw=lw, fill=False,color=color, zorder=zorder)
        
        # Left and right backboards
        l_backboard = Rectangle((4,-28), 0, 6, lw=lw, color=color, zorder=zorder)
        r_backboard = Rectangle((90, -28), 0, 6, lw=lw, color=color, zorder=zorder)

        # Left and right paint areas
        l_outer_box = Rectangle((0, -33), 19, 16, lw=lw, fill=False,
                                color=color, zorder=zorder)    
        l_inner_box = Rectangle((0, -31), 19, 12, lw=lw, fill=False,
                                color=color, zorder=zorder)
        r_outer_box = Rectangle((75, -33), 19, 16, lw=lw, fill=False,
                                color=color, zorder=zorder)

        r_inner_box = Rectangle((75, -31), 19, 12, lw=lw, fill=False,
                                color=color, zorder=zorder)

        # Left and right free throw circles
        l_free_throw = Circle((19,-25), radius=6, lw=lw, fill=False,
                              color=color, zorder=zorder)
        r_free_throw = Circle((75, -25), radius=6, lw=lw, fill=False,
                              color=color, zorder=zorder)

        # Left and right corner 3-PT lines
        # a is top lines
        # b is the bottom lines
        l_corner_a = Rectangle((0,-3), 14, 0, lw=lw, color=color,
                               zorder=zorder)
        l_corner_b = Rectangle((0,-47), 14, 0, lw=lw, color=color,
                               zorder=zorder)
        r_corner_a = Rectangle((80, -3), 14, 0, lw=lw, color=color,
                               zorder=zorder)
        r_corner_b = Rectangle((80, -47), 14, 0, lw=lw, color=color,
                               zorder=zorder)
        
        # Left and right 3-PT line arcs
        l_arc = Arc((5,-25), 47.5, 47.5, theta1=292, theta2=68, lw=lw,
                    color=color, zorder=zorder)
        r_arc = Arc((89, -25), 47.5, 47.5, theta1=112, theta2=248, lw=lw,
                    color=color, zorder=zorder)

        # half_court
        # ax.axvline(470)
        half_court = Rectangle((47,-50), 0, 50, lw=lw, color=color,
                               zorder=zorder)
        hc_big_circle = Circle((47, -25), radius=6, lw=lw, fill=False,
                               color=color, zorder=zorder)
        hc_sm_circle = Circle((47, -25), radius=2, lw=lw, fill=False,
                              color=color, zorder=zorder)
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

b=loaded(a.moments, a.pbp, a.home_team, a.away_team)

b.plot_frame(100)

# http://opiateforthemass.es/articles/animate-nba-shot-events/
        
        
   
        
        






