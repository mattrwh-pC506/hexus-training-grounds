"""Reinforcement learning agent."""


import numpy as np
from numba import jit 
import _thread
import datetime 
import json
import sys
from game.hexus import Hexus 
from game.qtable import end_transaction, QTable


class Agent(object):
    """Agent is the reinforcement learning agent that learns optimal state action pairs."""
    def __init__(self, Game, qtable=QTable(), player='B', learning_rate=5e-1, discount=9e-1, epsilon=8e-1, board_level="#EB00A2"):
        """Initialize agent with properties

        - qtable is json table with Q values Q(s,a)
        - game is reference to game being played
        - player is what player the agent is 'B', 'O', 'R', or 'P'
        - learning_rate is alpha value for gradient update
        - discount is discount factor for future expected rewards
        - epsilon is probability of exploration in epsilon greedy strategy
        """
        self.Game = Game
        self.qtable = qtable
        self.player = player
        self.learning_rate = learning_rate
        self.discount = discount
        self.epsilon = epsilon
        self.board_level = board_level

    def qvalue(self, state):
        """Retrieve value from qtable or initialize if not found."""
        if not self.qtable.get(state):
            self.qtable.set(state, 0.0)
        return self.qtable.get(state)

    def argmax(self, values):
        """Returns index of max value."""
        vmax = np.max(values)
        max_indices = []
        for i, v in enumerate(values):
            if v == vmax:
                max_indices.append(i)
        return np.random.choice(max_indices)

    def argmin(self, values):
        """Returns index of min value."""
        vmin = np.max(values)
        min_indices = []
        for i, v in enumerate(values):
            if v == vmin:
                min_indices.append(i)
        return np.random.choice(min_indices)

    def step(self, game, verbose=False):
        """Agent makes one step.

        - Deciding optimal or random action following e-greedy strategy given current state
        - Taking selected action and observing next state
        - Calculating immediate reward of taking action, current state, and next state
        - Updating q table values using GD with derivative of MSE of Q-value
        - Returns game status
        """
        old_board = [val for val in game.board]
        state, action = self.next_move(game)
        winner = game.make_move(action)
        reward = game.reward(winner)
        self.update(reward, winner, state, game)
        if verbose:
            print("=========")
            print(old_board)
            print(action)
            print(winner)
            print(state)
            print('Q value: {}'.format(self.qvalue(state)))
            game.print_board()
            print(reward)
        return (winner, reward)

    def next_move(self, game):
        """Selects next move in MDP following e-greedy strategy."""
        states, actions = game.get_open_moves()
        # print ([c[0].units for c in actions])
        # Exploit
        i = self.optimal_next(states, game)
        randolorian = np.random.random_sample()
        #if randolorian < self.epsilon:
        if True:
            if game.player == self.player: 
                self.clear_move_weights_of_tiles(actions)
                frontline_actions = [action for action in actions if action[0].team == self.player and action[0].team != action[1].team]
                self.add_move_weights_to_tiles(frontline_actions, 0)
                player_actions = [a for a in actions if a[0].team == self.player]
                sorted_actions_by_weight = sorted(player_actions, key=lambda a: a[0].weight, reverse=True)
                filtered_actions_by_direction = [a for a in sorted_actions_by_weight if a[0].weight - a[1].weight >= 0]
                actions_with_viable_moves = [a[0].weight for a in filtered_actions_by_direction if (a[0].units > 0 and a[1].units == 0 and a[1].team != self.player) or (a[0].units > 0 and a[1].units != 0 and a[1].team == self.player) or (a[0].units > 0 and a[0].weight == 1 and a[1].team != self.player)]
                if len(actions_with_viable_moves) > 0:
                    max_weight_with_units = max(actions_with_viable_moves)
                    filtered_actions_by_highest_weight = [a for a in filtered_actions_by_direction if a[0].weight == max_weight_with_units]
                    filtered_attack_actions = [action for action in filtered_actions_by_highest_weight if action[1].team != self.player]
                    actions_to_use = filtered_attack_actions if len(filtered_attack_actions) > 0 else filtered_actions_by_highest_weight
                    best_action = actions_to_use[np.random.randint(0, len(actions_to_use))]
                    i = actions.index(best_action)
                else:
                    i = np.random.randint(0, len(states))
            else: 
                i = np.random.randint(0, len(states))
        return states[i], actions[i]

    def clear_move_weights_of_tiles(self, actions):
        for action in actions:
            source_tile = action[0]
            source_tile.clear_weights()
            
    def add_move_weights_to_tiles(self, actions, weight):
        for action in actions:
            source_tile = action[0]
            source_tile.pulse_weights(weight)

    def optimal_next(self, states, game):
        """Selects optimal next move.

        Input
        - states list of possible next states
        Output
        - index of next state that produces maximum value
        """
        values = [self.qvalue(s) for s in states]
        # Exploit
        if game.player == self.player:
            # Optimal move is max
            return self.argmax(values)
        else:
            # Optimal move is min
            return self.argmin(values) 

    def update(self, reward, winner, state, game):
        """Updates q-value.

        Update uses recorded observations of performing a
        certain action in a certain state and continuing optimally from there.
        """
        # Finding estimated future value by finding max(Q(s', a'))
        # If terminal condition is reached, future reward is 0
        future_val = 0
        if not winner:
            future_states, _ = game.get_open_moves()
            i = self.optimal_next(future_states, game)
            future_val = self.qvalue(future_states[i])
        # Q-value update
        self.qtable.set(state, ((1 - self.learning_rate) * self.qvalue(state)) + (self.learning_rate * (reward + self.discount * future_val)))

    def train(self, episodes, history=[]):
        """Trains by playing against self.

        Each episode is a full game
        """
        x = range(episodes)
        cumulative_reward = []

        total_reward = 0.0
        for i in range(episodes):
            #total_reward = _thread.start_new_thread(self.play_game, (i, total_reward))
            total_reward = self.play_game(i, total_reward)
            cumulative_reward.append(total_reward)

        history.append(x)
        return history

    def play_game(self, episode, total_reward):
        game = Hexus(self.board_level)
        start = datetime.datetime.now()
        print("Game: " + str(episode + 1))
        episode_reward = 0.0
        game_active = True
        # Rest of game follows strategy
        winner = None
        while(game_active):
            """
            if game.get_all_units(self.player) == 0 and len(game.get_all_team_tiles(game.get_all_tiles(), self.player)) == 0:
                game_active = False
                game.reset()
            else:
                winner, reward = self.step(game)
                episode_reward += reward
                if winner:
                    game_active = False
                    game.reset()
            """
            # DELETE AFTER INITIAL EXPLORE TRAINING
            winner, reward = self.step(game)
            episode_reward += reward
            if winner:
                game_active = False
                game.reset()
            # DELETE AFTER INITIAL EXPLORE TRAINING

        total_reward += episode_reward
        end = datetime.datetime.now()
        str_elapsed = str(end - start)
        str_reward = str(episode_reward)
        print(f'winner: {winner}; reward: {str_reward}; timeElapsed: {str_elapsed}')
        end_transaction()
        return total_reward

    def stats(self):
        """Agent plays optimally against self with no exploration.

        Records win/loss/draw distribution.
        """
        b_wins = 0
        o_wins = 0
        r_wins = 0
        p_wins = 0
        draws = 0
        episodes = 10000
        for i in range(episodes):
            game = self.Game(self.board_level)
            game_active = True
            while(game_active):
                states, actions = game.get_open_moves()
                i = self.optimal_next(states, game)
                winner = game.make_move(actions[i])
                if winner:
                    if (winner == 'B'):
                        b_wins += 1 
                    elif (winner == 'O'):
                        o_wins += 1
                    elif (winner == 'R'):
                        r_wins += 1
                    elif (winner == 'P'):
                        p_wins += 1
                    else:
                        draws += 1
                    game_active = False
                    game.reset()
        print('    B: {} O: {} R: {} P: {}'.format((b_wins * 1.0) / episodes,
                                                (o_wins * 1.0) / episodes,
                                                (r_wins * 1.0) / episodes,
                                                (p_wins * 1.0) / episodes))
