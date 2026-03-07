from stable_baselines3 import DQN
from fsm_env import FSMEnv
from fsm_graph import build_fsm

# Build FSM graph
graph, flagged = build_fsm()

# Create environment
env = FSMEnv(graph, flagged)

# Load trained model
model = DQN.load("fsm_security_agent")

# Mitigation actions
actions = [
    "Insert Guard Condition",
    "Prune Transition",
    "Re-encode State",
    "Insert Deadlock Trap"
]

# Statistics counter
stats = {action: 0 for action in actions}

runs = 100

print("Running FSM Security Mitigation Evaluation\n")

for i in range(runs):

    obs, _ = env.reset()

    action, _ = model.predict(obs, deterministic=False)

    action_name = actions[int(action)]

    stats[action_name] += 1

    print(f"Run {i+1}")
    print("Observation:", obs.tolist())
    print("Chosen Action:", action_name)
    print("------------------------")

    env.step(action)

# ---- STATISTICS ----

print("\n===================================")
print("FSM Vulnerability Mitigation Stats")
print("===================================\n")

for action in actions:
    count = stats[action]
    percent = (count / runs) * 100

    print(f"{action}: {count} times ({percent:.2f}%)")