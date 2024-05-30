# Game data.
# Written by Tiago Perez

import csv

class GameData:
    def __init__(self, file_path):
        self.data = {}
        self.load_data(file_path)
        self.max_time = max(self.data.keys())

    def load_data(self, file_path):
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                time = int(row['time'])
                team = row['team']
                player_id = int(row['player_id'])
                x = int(row['x'])
                y = int(row['y'])
                if time not in self.data:
                    self.data[time] = {'team1': [], 'team2': [], 'ball': []}
                if team == 'ball':
                    self.data[time][team] = [(x, y)]
                else:
                    self.data[time][team].append((x, y, player_id))

    def get_positions(self, time):
        return self.data.get(time, {'team1': [], 'team2': [], 'ball': [(0, 0)]})
