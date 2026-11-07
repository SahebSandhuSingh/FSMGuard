import networkx as nx

def build_fsm():

    G = nx.DiGraph()

    # Example FSM transitions
    G.add_edge("S0", "S1")
    G.add_edge("S1", "S2")
    G.add_edge("S2", "S3")
    G.add_edge("S3", "S1")   # loop
    G.add_edge("S1", "S4")

    flagged_state = "S1"

    return G, flagged_state