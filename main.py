"""Train Reinforcement Learning agent.

To run:
    python main.py

"""


import argparse
import sys
import matplotlib.pyplot as plt
import ujson as json

from game.hexus import Hexus 
from rl.agent import Agent


def process_args():
    """Process command line args."""
    message = 'Interactive Reinforcement Learning board game playing agent.'
    parser = argparse.ArgumentParser(description=message)

    default_game = 'tictactoe'
    default_mode = 'train'
    default_episodes = 10000 
    default_board_level = '#EB00A2'

    parser.add_argument('-g', '--game',
                        dest='game',
                        help='Board game choice.',
                        default=default_game)

    parser.add_argument('-m', '--mode',
                        dest='mode',
                        help='Mode for Agent can be ["train"].',
                        default=default_mode)
    
    parser.add_argument('-bl', '--board_level',
                        dest='board_level',
                        help='Board for Agent can be ["#EB00A2", "#0D2EFF", "#00FF94", "#8700EB", "#FFFFFF", "#000000"].',
                        default=default_board_level)

    parser.add_argument('-e', '--episodes',
                        dest='episodes',
                        help='Episodes for Agent can be [0-n].',
                        default=default_episodes)

    options = parser.parse_args()
    return options

def play_hexus(mode, episodes, board_level):
    print('<><><><>HEXUS<><><><>')
    if mode == 'train':
        # Train agent to go first
        agent = Agent(Hexus, epsilon=5e-1, learning_rate=25e-2, board_level=board_level)
        n = episodes
        history = agent.train(n)
        print('After {} Episodes'.format(n))

    elif mode == 'hyper':
        # Hyper parameter optimization
        max_e = 0.0
        max_lr = 0.0
        max_reward = 0.0
        epsilons = [1e-1, 2e-1, 9e-2, 1e-2, 9e-3]
        learning_rates = [1e-1, 2e-1, 3e-1, 25e-2, 9e-2]
        for epsilon in epsilons:
            for learning_rate in learning_rates:
                agent = Agent(Hexus, qtable={}, player='B', epsilon=epsilon, learning_rate=learning_rate)
                n = 10000
                history = agent.train(n, history=[])
                total = history[1][len(history[1]) - 1]
                print(total)
                if total > max_reward:
                    max_reward = total
                    max_e = epsilon
                    max_lr = learning_rate
        print('Max e: {}'.format(max_e))
        print('Max lr: {}'.format(max_lr))
        print('Max reward: {}'.format(max_reward))

    else:
        print('Mode {} is invalid.'.format(mode))


def main():
    """Entry point."""
    options = process_args()
    if options.game == 'hexus':
        play_hexus(options.mode, int(options.episodes), options.board_level)
    else:
        print('Game choice {} is current unsupported.'
              .format(options.game))
        sys.exit(1)


if __name__ == '__main__':
    main()
