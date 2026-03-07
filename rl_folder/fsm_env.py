import gymnasium as gym
from gymnasium import spaces
import numpy as np
import random


class FSMEnv(gym.Env):

    def __init__(self, graph, flagged_node):

        super(FSMEnv, self).__init__()

        self.graph = graph
        self.node = flagged_node

        self.observation_space = spaces.Box(
            low=0,
            high=20,
            shape=(7,),
            dtype=np.float32
        )

        self.action_space = spaces.Discrete(4)

    def extract_features(self):

        in_edges = self.graph.in_degree(self.node)
        out_edges = self.graph.out_degree(self.node)

        neighbors = len(list(self.graph.neighbors(self.node)))

        loop = int(self.graph.has_edge(self.node, self.node))

        deadlock = int(out_edges == 0)

        privileged = int(in_edges > 2)

        unreachable = 0

        features = np.array([
            in_edges,
            out_edges,
            neighbors,
            loop,
            deadlock,
            privileged,
            unreachable
        ], dtype=np.float32)

        return features

    def reset(self, seed=None, options=None):

        self.node = random.choice(list(self.graph.nodes))

        obs = self.extract_features()

        return obs, {}

    def step(self, action):

        reward = 0

        if action == 0:
            reward = 8
        elif action == 1:
            reward = 10
        elif action == 2:
            reward = 5
        elif action == 3:
            reward = 6

        obs = self.extract_features()

        done = True

        return obs, reward, done, False, {}