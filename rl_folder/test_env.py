from fsm_env import FSMEnv
from fsm_graph import build_fsm

graph, flagged = build_fsm()

env = FSMEnv(graph, flagged)

obs, _ = env.reset()

print("Initial Observation:", obs)

for action in range(4):

    obs, reward, done, _, _ = env.step(action)

    print("Action:", action)
    print("Observation:", obs)
    print("Reward:", reward)
    print("Done:", done)
    print("------------")