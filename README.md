# NBA player tracking visualization and analysis

This library contains useful methods for visualizing and analyzing NBA player tracking data.

TODO: add links
The data is located here and contains all player and ball locations for NBA games from the 2015-16 season.  Play-by-play data is obtained from nba.stats.com.

## Visualization
To visualize games from the tracking data, the `game` class in `game.py` is used.
```python
from Game import game
game_data = game()
game.watch_play()
```

To easily follow the flow of the game, commentary can be added.
```python
game.watch_play(commentary=True)
```

If you are interested in a single player, they can easily be tracked.
```python
game.watch_play(highlight_player="Stephen Curry", commentary=False)
```

All of a players actions can be extracted and viewed with a single method call.
```python
game.watch_player_actions("Stephen Curry", "made_FG")
```

## Analysis

### Defensive Spacing

### Player Velocity
