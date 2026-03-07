from stable_baselines3 import DQN
from fsm_env import FSMEnv
from fsm_graph import build_fsm

graph, flagged = build_fsm()

env = FSMEnv(graph, flagged)

model = DQN(
    "MlpPolicy",
    env,
    verbose=1
)

model.learn(total_timesteps=100000)

model.save("fsm_security_agent")

print("Model trained and saved")