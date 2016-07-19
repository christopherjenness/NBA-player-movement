a = Game('01.03.2016', 'DEN', 'POR')

home_offense_areas, home_defense_areas, away_offense_areas, away_defense_areas = [], [], [], []

for frame in range(len(b.moments)):
    offensive_team = b.get_offensive_team(frame)
    if offensive_team == 'home':
        home_offense_area, away_defense_area = b.get_spacing_area(frame)
        home_offense_areas.append(home_offense_area)
        away_defense_areas.append(away_defense_area)
    if offensive_team == 'away':
        home_defense_area, away_offense_area = b.get_spacing_area(frame)
        home_defense_areas.append(home_defense_area)
        away_offense_areas.append(away_offense_area)
    if frame % 1000 == 0:
        print(frame)
        
        