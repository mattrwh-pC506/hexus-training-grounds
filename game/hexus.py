import time
import math
from .game import Game
from .qtable import load_board_configs_to_db_from_json, get_board_config, begin_transaction, new_transaction
import sys
import pydash

class Tile:

    def __init__(self, game, team, x, y, units):
        self.game = game 
        self.team = team
        self.x = x
        self.y = y
        self.units = units

    def to_string(self, game, neighbors):
        if len(neighbors):
            weights = [(neighbor.x, neighbor.y, self.determine_weight(neighbor), neighbor.units) for neighbor in neighbors]
            sum_of_move_weights = sum(w[2] for w in weights) / len(neighbors)
            move_weight_lean = 1 if sum_of_move_weights > 0 else 0 if sum_of_move_weights == 0 else -1
            return f'{self.team}({self.x},{self.y}):{move_weight_lean}'
        else:
            return ''

    def determine_weight(self, neighbor):
        neighbor_clone = neighbor.clone()
        self.handle_move_scenario(neighbor_clone, self.clone())
        return 1 if neighbor_clone.team == self.team else 0 if neighbor_clone.units == self.units else -1

    def clone(self):
        return Tile(self.game, self.team, self.x, self.y, self.units)
    
    def handle_move_scenario(self, target_tile, source_tile=None, real=False):
        source_tile = source_tile or self
        if target_tile.team ==  source_tile.team:
            target_tile.units = target_tile.units + source_tile.units 
            source_tile.units = 0
        else:
            leftover_units = target_tile.units - source_tile.units
            if leftover_units >= 0:
                target_tile.units = leftover_units
                source_tile.units = 0
            else:
                target_tile.team = source_tile.team
                target_tile.units = abs(leftover_units)
                source_tile.units = 0
    
    def get_neighbors(self):
        return pydash.compact([self.NE, self.NW, self.SE, self.SW, self.E, self.W ])
    
    _weight = sys.maxsize

    @property
    def weight(self): return self._weight

    @weight.setter
    def weight(self, w): 
        if w < self.weight: 
            self._weight = w 
            self.pulse_weights(w) 
    
    def pulse_weights(self, weight=0):
        self.get_neighbors()
        for neighbor in self.get_neighbors():
            if neighbor.team != self.game.player:
                neighbor.weight = 0
            else:
                neighbor.weight = (weight + 1)
    
    @property
    def NE(self): 
        tile = self.game.board.get(f'{self.x + 6},{self.y + 9}')
        if tile and tile.team != 'X': return tile 
        else: return None
    @property
    def NW(self): 
        tile = self.game.board.get(f'{self.x - 6},{self.y + 9}')
        if tile and tile.team != 'X': return tile 
        else: return None
    @property
    def SE(self):  
        tile = self.game.board.get(f'{self.x + 6},{self.y - 9}')
        if tile and tile.team != 'X': return tile 
        else: return None
    @property
    def SW(self):  
        tile = self.game.board.get(f'{self.x - 6},{self.y - 9}')
        if tile and tile.team != 'X': return tile 
        else: return None
    @property
    def E(self):  
        tile = self.game.board.get(f'{self.x + 12},{self.y}')
        if tile and tile.team != 'X': return tile 
        else: return None
    @property
    def W(self):  
        tile = self.game.board.get(f'{self.x - 12},{self.y}')
        if tile and tile.team != 'X': return tile 
        else: return None 

    def clear_weights(self):
        self._weight = sys.maxsize

class Hexus(Game):
    round_starting_units = 2
    rounds = 1
    # DEFAULT_PLAYERS = ['B', 'R', 'O', 'P']
    # DELETE AFTER INITIAL EXPLORE TRAINING
    DEFAULT_PLAYERS = ['B']
    # DELETE AFTER INITIAL EXPLORE TRAINING
    PLAYERS = []
    EMPTY_BOARD = lambda self: self.build_default_board()
 
    def __init__(self, board_level):
        self.board_level = board_level
        begin_transaction()
        load_board_configs_to_db_from_json()
        new_transaction()
        self.reset()
        new_transaction()

    def build_default_board(self):
        config = get_board_config(self.board_level)
        board_team_array = config[1]
        board_width = board_team_array.index("O") + 1
        board_height = 9 
        board = {}
        odd_row_x_starting_position = (-1 * (board_width / 2 if board_width % 2 == 0 else (board_width - 1) / 2)) * 12
        even_row_x_starting_position = odd_row_x_starting_position + 6
        y_starting_position = (board_height / 2 if board_height % 2 == 0 else (board_height - 1) / 2) * 9
        current_x = odd_row_x_starting_position
        current_y = y_starting_position
        for i, team in enumerate(board_team_array):
            i += 1
            if team != 'X':
                board[f"{current_x},{current_y}"] = Tile(self, team, current_x, current_y, 1 if team == 'U' else 2)
            
            row_set_width = board_width + (board_width - 1)
            i_within_set = i % row_set_width
            is_odd_row = i_within_set != 0 and i_within_set <= board_width 
            is_even_row = not is_odd_row 
            if (is_odd_row and i_within_set != board_width) or (is_even_row and i_within_set != 0):
                current_x += 12
            else:
                current_y -= 9 
                current_x = odd_row_x_starting_position if is_even_row else even_row_x_starting_position
        return board

    def reset(self):
        self.PLAYERS = self.DEFAULT_PLAYERS 
        self.board = {self.build_lookup_key(tile): tile for tile in self.EMPTY_BOARD().values()}
        self.player = 'B'

    def get_open_moves(self):
        actions = []
        states = []
        all_tiles = self.get_all_tiles()
        team_tiles = self.get_all_team_tiles(all_tiles)
        for i, tile in enumerate(team_tiles):
            if tile.units > 0: 
                valid_move_tiles = tile.get_neighbors()
                for move in valid_move_tiles: 
                    source_tile = self.board.get(self.build_lookup_key(tile))
                    target_tile = self.board.get(self.build_lookup_key(move))
                    actions.append((source_tile, target_tile))
                    states.append(self.get_state(self.board))
        return states, actions

    def build_lookup_key(self, tile):
        return f'{tile.x},{tile.y}'

    def cloned_board(self):
        return {self.build_lookup_key(tile): Tile(tile.game, tile.team, tile.x, tile.y, tile.units) for tile in self.board.values()}

    def get_all_tiles(self):
        return [tile for tile in self.board.values()]

    def get_all_team_tiles(self, all_tiles, team=None):
        team = team or self.player
        return [team_tile for team_tile in all_tiles if team_tile.team == team]

    def get_state(self, board):
        all_tiles = self.get_all_tiles()
        team_tiles = self.get_all_team_tiles(all_tiles)
        total_units = sum(tile.units for tile in all_tiles)
        total_team_units = sum(tile.units for tile in team_tiles)
        all_tile_count = len(all_tiles)
        team_tile_count = len(team_tiles)
        return ';'.join(tile.to_string(self, tile.get_neighbors()) for tile in self.get_all_tiles())

    def is_win(self):
        team_to_check = None
        for tile in self.get_all_tiles():
            if team_to_check is None and tile.team != 'U':
                team_to_check = tile.team
            elif tile.team != 'U':
                if team_to_check != tile.team:
                    return None
            
        return team_to_check

    def make_move(self, move):
        #self.print_board()
        move_source_tile, move_target_tile = move
        source_tile = self.board.get(self.build_lookup_key(move_source_tile))
        target_tile = self.board.get(self.build_lookup_key(move_target_tile))
        source_tile.handle_move_scenario(target_tile, source_tile, True)
        leftover_units = self.get_all_units()
        ratio_spent = leftover_units / self.round_starting_units
        # print (ratio_spent, leftover_units, self.round_starting_units)
        #if ratio_spent < 0.1: 
        #    self.next_round()
        if leftover_units == 0:
            self.next_round()
        #self.print_board()
        #time.sleep(10)
        return self.is_win() 

    def next_round(self):
        """
        players_to_check = [p for p in self.PLAYERS]
        for player in players_to_check:
            is_active = not not sum([1 for tile in  self.get_all_tiles() if tile.team == player])
            if (not is_active): 
                self.PLAYERS.remove(player)
        next_team_index = (self.PLAYERS.index(self.player) + 1) % len(self.PLAYERS)
        next_team = self.PLAYERS[next_team_index]
        self.player = next_team
        """
        team_tiles = self.get_all_team_tiles(self.get_all_tiles())
        for tile in team_tiles:
            tile.units += 1
        all_tiles = self.get_all_tiles()
        b_units = self.get_all_units('B')
        b_tiles = len(self.get_all_team_tiles(all_tiles, 'B'))
        r_units = self.get_all_units('R')
        r_tiles = len(self.get_all_team_tiles(all_tiles, 'R'))
        o_units = self.get_all_units('O')
        o_tiles = len(self.get_all_team_tiles(all_tiles, 'O'))
        p_units = self.get_all_units('P')
        p_tiles = len(self.get_all_team_tiles(all_tiles, 'P'))
        self.round_starting_units = self.get_all_units()
        self.rounds += 1
        print(f'B({b_tiles},{b_units});R({r_tiles},{r_units});O({o_tiles},{o_units});P({p_tiles},{p_units})', end='\r')

    def get_all_units(self, team=None):
        return sum(tile.units for tile in self.get_all_team_tiles(self.get_all_tiles(), team))
    
    def reward(self, winner):
        """Calculates reward for different end game conditions.

        - win is 1.0
        - loss is -1.0
        - draw and unfinished is 0.0
        """
        players = self.DEFAULT_PLAYERS 
        trained_player = 'B'
        opponents = filter(lambda x: x != trained_player, players)

        all_tiles = self.get_all_tiles()
        trained_player_units = self.get_all_units(trained_player)
        trained_player_tiles = len(self.get_all_team_tiles(all_tiles, trained_player))

        if winner == trained_player:
            return 1.0
        elif (winner in opponents) or (trained_player_units == 0 and trained_player_tiles == 0):
            return -1.0
        else:
            return 0


    def print_board(self):
        config = get_board_config(self.board_level)
        board_team_array = config[1]
        board_width = board_team_array.index("O") + 1
        board_height = 9 
        odd_row_x_starting_position = (-1 * (board_width / 2 if board_width % 2 == 0 else (board_width - 1) / 2)) * 12
        even_row_x_starting_position = odd_row_x_starting_position + 6
        y_starting_position = (board_height / 2 if board_height % 2 == 0 else (board_height - 1) / 2) * 9
        current_x = odd_row_x_starting_position
        current_y = y_starting_position
        str_board = ''
        for i, team in enumerate(board_team_array):
            i += 1
            tile = None 
            if team != 'X':
                tile = self.board.get(f"{current_x},{current_y}")
                str_board += f"[{tile.team}:{tile.weight if tile.weight < 100 else 'X'}:{tile.units}]"
            
            row_set_width = board_width + (board_width - 1)
            i_within_set = i % row_set_width
            is_odd_row = i_within_set != 0 and i_within_set <= board_width 
            is_even_row = not is_odd_row 
            if (is_odd_row and i_within_set != board_width) or (is_even_row and i_within_set != 0):
                current_x += 12
            else:
                current_y -= 9 
                current_x = odd_row_x_starting_position if is_even_row else even_row_x_starting_position
                str_board += "\n"
                if is_odd_row:
                    str_board += "   "
        print (str_board)
