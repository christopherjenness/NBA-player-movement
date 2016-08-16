# NBA player tracking visualization and analysis

This library contains useful methods for visualizing and analyzing NBA player tracking data.

The data is located here and contains all player and ball locations for NBA games from the 2015-16 season.  Play-by-play data is obtained from nba.stats.com.

## Visualization
To visualize games from the tracking data, the `game` class in `game.py` is used.
```python
from Game import game
game = Game('01.08.2016', 'POR', 'GSW')
game.watch_play(game_time=6, length=120, commentary=False)
```
![NoCommentary](examples/GSWatPORnocommentary.gif)

To easily follow the flow of the game, commentary can be added.
```python
game.watch_play(game_time=6, length=120, commentary=True)
```

![Commentary](examples/GSWatPOR.gif)

If you are interested in a single player, they can easily be tracked.
```python
game.watch_play(2007, 10, highlight_player='Stephen Curry', commentary=False)
```

![Curry3](examples/Curry3.gif)

All of a players actions can be extracted and viewed with a single method call.
```python
game.watch_player_actions("Stephen Curry", "made_FG")
```

## Analysis

Here, we analyze two aspects of basketball that are difficult to address without player tracking data:
* Defensive Spacing
* Player/Team Velocity

### Defensive Spacing

NBA commentators often praise offensive teams who can "Space the defense".  Essentially, if an offensive team can draw out defenders to the three point line, passing lanes will open up and drives to the basket will be less clogged and more efficient.  Here we analyze how effectively teams can space the defense.  

The workhorse of this analysis is `scipy.spatial.ConvexHull` which measures the convex hull of the defense (larger convex hull = more spaced defense).  This can be visualized:

```python
game.watch_play(show_spacing='GSW')
```

`spacing_analysis.py` contains the code for the following analysis.  To process the data, only "set plays" were analyzed.  Since "transition plays" has unique spacing properties, we limited this analysis to "standard" plays where the offense and defense are set.

Which teams are best at spacing the defense? (Remember, spacing the defense more is thought to be better).  If we average over all time points for each team, we get the following:

http://www.sbnation.com/nba/2015/1/9/7517125/detroit-pistons-winning-streak-josh-smith-released

Interestingly, we see that Detroit is the best team at spacing defenses.  This is something that has been anecdotally documented by Mike Prada, and the data back up his claims.  Additionally, teams like San Antonio that are thought to have a modern offense, are great at spacing the defense.  

But the question is: **Does spacing the defense help you win?**  Here we look at the score differential vs defensive spacing and we see a positive correlation.  In fact, spacing the defense an extra [X] square feet correlates with increasing the score differential [X] points! 

If you stare at this graph long enough, you can notice it also shows the level of home court advantage in the NBA.  If you are interested, you can read an analysis of home court advantage I did here.

**How can a team space the defense better?**  Intuitively, spacing your offense will draw out the defense.  This is true with some interesting exceptions.

Notice Toronto.  Toronto has a hard time spacing the defense even though they space out their offense.  This is likely due to their star DeMar DeRozan being a shooting liability.  Defender's don't need to guard him out on the 3PT line, so they can keep the paint clogged.

Notice San Antonio.  San Antonio can effectively space the defense without spacing out their offense.  May be due to having one of the best 3PT shooters in the league, Kawhi Leonard, who needs be guarded religiously at the 3PT line.

**Can more efficient 3PT shooting space the defense?**  It appears so.  Taking more 3 point shoots, or taking them at a higher percentage correlate with effective defensive spacing.

Currently, I'm working on breaking down defensive spacing per play, so see the effect on individual plays instead of aggregated game data.  This is yielding interesting insights.

### Player Velocity
