import sqlite3
import json
import re


db = sqlite3.connect('game/qtable.db')

def begin_transaction():
    db.execute("BEGIN TRANSACTION")

def update_qtable(key, weight, player):
    db.execute(f"INSERT OR REPLACE INTO qtable (key, weight, player) VALUES ('{key}', {weight}, '{player}');")

def end_transaction():
    db.commit()

def new_transaction():
    end_transaction()
    begin_transaction()

def load_board_configs_to_db_from_json(path='game/board_levels.json'):
    with open(path) as json_file:
        data = json.load(json_file)
        db.execute(f"CREATE TABLE IF NOT EXISTS board_level ( name text PRIMARY KEY, board text NOT NULL);")
        for l in data['levels']:
            db.execute(f"INSERT OR REPLACE INTO board_level (name, board) VALUES (?, ?);", (l["name"], "".join(l["board"]),))

def get_board_config(name):
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM board_level WHERE name=:name", {"name": name,})
    board = cursor.fetchone()
    cursor.close()
    return board


class QTable:
    def get(self, key):
        cursor = db.cursor()
        cursor.execute("SELECT * FROM qtable WHERE key=:key", {"key": key})
        res = cursor.fetchone()
        if res: return res[1]
        else: return None 

    def set(self, key, weight):
        [b, o, r, p] = self.build_keys_for_opposition(key)
        update_qtable(b, weight, 'B')
        update_qtable(o, weight, 'O')
        update_qtable(r, weight, 'R')
        update_qtable(p, weight, 'P')

    def build_keys_for_opposition(self, key):
        board = self.parse_key(key)
        o_player_as_b = self.rebuild_key(self.swap_coord(self.swap_teams(board, 'O', 'B', 'P', 'R'), 'O'))
        r_player_as_b = self.rebuild_key(self.swap_coord(self.swap_teams(board, 'R', 'P', 'B', 'O'), 'R'))
        p_player_as_b = self.rebuild_key(self.swap_coord(self.swap_teams(board, 'P', 'R', 'O', 'B'), 'P'))
        return [key, o_player_as_b, r_player_as_b, p_player_as_b]
    
    def parse_key(self, key):
        return [[tile[0], tile[1:]] for tile in key.split(";")]

    def rebuild_key(self, board):
        return ";".join(tile[0] + tile[1:] for tile in board)
    
    def swap_teams(self, board, top_left, top_right, bottom_left, bottom_right):
        for t in board:
            if t[0] == 'B':
                t[0] = top_left
            elif t[0] == 'O':
                t[0] = top_right
            elif t[0] == 'R':
                t[0] = bottom_left
            elif t[0] == 'P':
                t[0] = bottom_right
        return board

    def swap_coord(self, board, player):
        new_board = []
        for tile in board:
            units = tile[1].split(":")[1]
            split_tile = re.search("\((.+?)\)", tile[1]).group(1)
            x, y = map(lambda i: float(i), split_tile.split(","))
            if player == 'O':
                x *= -1
            elif player == 'R':
                y *= -1
            elif player == 'P':
                x *= -1
                y *= -1
            
            new_board.append(f"{tile[0]}({x},{y}):{units}")
        return new_board



