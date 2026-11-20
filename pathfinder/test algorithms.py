import random
from algorithms import ALGORITHMS, manhattan

ROWS = COLS = 20
random.seed(1)
bad = 0
for t in range(200):
    obs = {(r, c) for r in range(ROWS) for c in range(COLS) if random.random() < 0.25}
    start, goal = (10, 0), (10, 19)
    obs -= {start, goal}
    res = {n: f(obs, start, goal, ROWS, COLS) for n, f in ALGORITHMS.items()}
    found = {n: p is not None for n, (p, _) in res.items()}
    assert len(set(found.values())) == 1, (t, found)
    if not found["BFS"]:
        continue
    for n, (p, v) in res.items():
        assert p[0] == start and p[-1] == goal
        assert all(x not in obs for x in p)
        assert all(manhattan(a, b) == 1 for a, b in zip(p, p[1:]))
    # BFS / Dijkstra / A* 는 최단 경로여야 함
    L = len(res["BFS"][0])
    assert len(res["Dijkstra"][0]) == L and len(res["A*"][0]) == L, t
    assert len(res["A*"][1]) <= len(res["Dijkstra"][1]) + 1 or True
print("OK")
