import sqlite3
import json


db = sqlite3.connect('game/qtable.db')

def begin_transaction():
    db.execute("BEGIN TRANSACTION")

def update_qtable(key, weight):
    db.execute(f"INSERT OR REPLACE INTO qtable (key, weight) VALUES ('{key}', {weight});")

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
