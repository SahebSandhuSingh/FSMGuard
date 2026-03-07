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

    # ✅ THIS FUNCTION MUST EXIST
    def extract_features(self):

        in_edges = self.graph.in_degree(self.node)
        out_edges = self.graph.out_degree(self.node)

        neighbors = list(self.graph.neighbors(self.node))

        loop = 1 if self.graph.has_edge(self.node, self.node) else 0

        features = np.array([
            in_edges,
            out_edges,
            len(neighbors),
            loop,
            1 if out_edges > 3 else 0,
            0,
            0
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