from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from tensorforce import TensorForceError
from tensorforce.agents import Agent
from tensorforce.execution import Runner
from src.environment import ReJoin
from src.database import Database
from tensorforce.agents import PPOAgent

# from src.distribution import CustomCategorical

import argparse
import logging
import sys
import time
import json

sys.argv = [""]


def make_args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--agent-config",
        default="config/ppo.json",
        help="Agent configuration file",
    )
    parser.add_argument(
        "-n",
        "--network-spec",
        default="config/mlp2-network.json",
        help="Network specification file",
    )
    parser.add_argument(
        "-rap",
        "--repeat-action-probability",
        help="Repeat action probability",
        type=float,
        default=0.0,
    )
    parser.add_argument(
        "-e", "--episodes", type=int, default=1000, help="Number of episodes"
    )
    parser.add_argument(
        "-t",
        "--max-timesteps",
        type=int,
        default=20,
        help="Maximum number of timesteps per episode",
    )
    parser.add_argument("-s", "--save", help="Save agent to this dir")
    parser.add_argument(
        "-se",
        "--save-episodes",
        type=int,
        default=100,
        help="Save agent every x episodes",
    )
    parser.add_argument("-l", "--load", help="Load agent from this dir")
    parser.add_argument("-p", "--phase", help="Select phase (1 or 2)", default=1)

    return parser.parse_args()


def print_config(args):
    print("Running with the following configuration")
    arg_map = vars(args)
    for key in arg_map:
        print("\t", key, "->", arg_map[key])


def main():
    args = make_args_parser()
    # print_config(args)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))

    # Connect to database
    db = Database()
    # get_times()

    # ~~~~~~~~~~~~~~~~~ Setting up the Model ~~~~~~~~~~~~~~~~~ #

    # Initialize environment (tensorforce's template)
    environment = ReJoin(db, args.phase)

    if args.agent_config is not None:
        with open(args.agent_config, "r") as fp:
            agent_config = json.load(fp=fp)
    else:
        raise TensorForceError("No agent configuration provided.")

    if args.network_spec is not None:
        with open(args.network_spec, "r") as fp:
            network_spec = json.load(fp=fp)
    else:
        raise TensorForceError("No network configuration provided.")

    dims = 128
    # Todo: Pass this via JSON
    network_spec = [
        [
            dict(type="input", names=["tree_structure"]),
            dict(type="flatten"),
            dict(type="dense", size=dims, activation="relu"),
            dict(type="output", name="tree_structure_emb"),
        ],
        [
            dict(type="input", names=["join_predicates"]),
            dict(type="flatten"),
            dict(type="dense", size=dims, activation="relu"),
            dict(type="output", name="join_predicates_emb"),
        ],
        [
            dict(type="input", names=["selection_predicates"]),
            dict(type="dense", size=dims, activation="relu"),
            dict(type="output", name="selection_predicates_emb"),
        ],
        [
            dict(
                type="input",
                names=[
                    "tree_structure_emb",
                    "join_predicates_emb",
                    "selection_predicates_emb",
                ],
            ),
            dict(type="dense", size=dims, activation="relu"),
            dict(type="dense", size=dims, activation="relu"),
            # dict(type='dueling', size=3, activation='none'),
            dict(type="output", name="prediction"),
        ],
    ]

    # Set up the PPO Agent
    agent = PPOAgent(
        states=environment.states,
        actions=environment.actions,
        network=network_spec,
        step_optimizer=dict(type="adam", learning_rate=1e-3),
        # distributions=dict(action=dict(type=CustomCategorical)),
    )

    # agent = Agent.from_spec(
    #     spec=agent_config,
    #     kwargs=dict(
    #         states=environment.states, actions=environment.actions, network=network_spec
    #     ),
    # )

    runner = Runner(agent=agent, environment=environment)

    # ~~~~~~~~~~~~~~~~~ ~~~~~~~~~~~~~~~~~~~~~ ~~~~~~~~~~~~~~~~~ #

    report_episodes = 1

    def episode_finished(r):
        if r.episode % report_episodes == 0:
            sps = r.timestep / (time.time() - r.start_time)
            logger.info(
                "Finished episode {ep} after {ts} timesteps. Steps Per Second {sps}".format(
                    ep=r.episode, ts=r.timestep, sps=sps
                )
            )
            logger.info("Episode reward: {}".format(r.episode_rewards[-1]))
            logger.info(
                "Average of last 500 rewards: {}".format(
                    sum(r.episode_rewards[-500:]) / 500
                )
            )
            logger.info(
                "Average of last 100 rewards: {}".format(
                    sum(r.episode_rewards[-100:]) / 100
                )
            )
        return True

    logger.info("Starting {agent} for Environment '{env}'".format(agent=agent, env=environment))

    # Start Training
    runner.run(
        episodes=500,
        max_episode_timesteps=args.max_timesteps,
        episode_finished=episode_finished,
    )

    runner.close()
    logger.info("Learning finished. Total episodes: {ep}".format(ep=runner.episode))

    # environment.close()
    # print(runner.episode_rewards)
    # print(len(runner.episode_rewards))
    def find_convergence(eps):
        last = eps[-1]
        for i in range(1, len(eps)):
            if eps[i * -1] != last:
                print("Converged at episode:", len(eps) - i + 2)
                return True

    find_convergence(runner.episode_rewards)
    db.close()


if __name__ == "__main__":
    main()
