from stable_baselines3 import DQN
from fsm_env import FSMEnv
from fsm_graph import build_fsm

def run_model():
    # Build FSM graph
    graph, flagged = build_fsm()

    # Create environment
    env = FSMEnv(graph, flagged)

    # Load trained model
    model = DQN.load("rl_folder/fsm_security_agent")

    # Mitigation actions
    actions = [
        "Insert Guard Condition", 
        "Prune Transition", 
        "Re-encode State", 
        "Insert Deadlock Trap"
    ]

    # Statistics counter
    stats = {action: 0 for action in actions}
    runs = 10
    results = []

    # --- START OF RUN LOOP ---
    for i in range(runs):
        obs, _ = env.reset()
        action, _ = model.predict(obs, deterministic=False)
        action_name = actions[int(action)]

        # ✅ PRINT STATEMENT PLACED HERE TO SHOW ALL 10 RUNS
        print(f"Run {i+1}/10 | Action: {action_name} | Obs: {obs.tolist()}")

        stats[action_name] += 1

        results.append({
            "run": i + 1,
            "observation": obs.tolist(),
            "action": action_name
        })

        env.step(action)
    # --- END OF RUN LOOP ---

    summary = []

    for action in actions:
        count = stats[action]
        percent = (count / runs) * 100

        summary.append({
            "action": action,
            "count": count,
            "percentage": percent
        })

    return {
        "runs": results,
        "stats": summary
    }