"""길찾기 알고리즘 모음 (pygame 의존성 없음).

모든 알고리즘은 같은 형태를 따릅니다.
    algo(obstacles, start, goal, rows, cols) -> (path | None, visited_order)
- obstacles: {(row, col), ...} 장애물 좌표 집합
- path: start~goal 좌표 리스트 (길이 없으면 None)
- visited_order: 탐색(확장)한 노드를 순서대로 담은 리스트
"""
import heapq
from collections import deque

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def neighbors(obstacles, node, rows, cols):
    r, c = node
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in obstacles:
            yield (nr, nc)


def build_path(parent, goal):
    path, cur = [], goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    return path[::-1]


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def bfs(obstacles, start, goal, rows, cols):
    queue = deque([start])
    parent = {start: None}
    visited = []
    while queue:
        cur = queue.popleft()
        visited.append(cur)
        if cur == goal:
            return build_path(parent, goal), visited
        for n in neighbors(obstacles, cur, rows, cols):
            if n not in parent:
                parent[n] = cur
                queue.append(n)
    return None, visited


def dfs(obstacles, start, goal, rows, cols):
    stack = [start]
    parent = {start: None}
    seen = set()
    visited = []
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        visited.append(cur)
        if cur == goal:
            return build_path(parent, goal), visited
        for n in neighbors(obstacles, cur, rows, cols):
            if n not in seen:
                parent[n] = cur
                stack.append(n)
    return None, visited


def dijkstra(obstacles, start, goal, rows, cols):
    heap = [(0, 0, start)]
    dist = {start: 0}
    parent = {start: None}
    done = set()
    visited = []
    count = 0
    while heap:
        d, _, cur = heapq.heappop(heap)
        if cur in done:
            continue
        done.add(cur)
        visited.append(cur)
        if cur == goal:
            return build_path(parent, goal), visited
        for n in neighbors(obstacles, cur, rows, cols):
            nd = d + 1  # 모든 칸 이동 비용 1
            if nd < dist.get(n, float("inf")):
                dist[n] = nd
                parent[n] = cur
                count += 1
                heapq.heappush(heap, (nd, count, n))
    return None, visited


def astar(obstacles, start, goal, rows, cols):
    heap = [(manhattan(start, goal), 0, start)]
    g = {start: 0}
    parent = {start: None}
    done = set()
    visited = []
    count = 0
    while heap:
        _, _, cur = heapq.heappop(heap)
        if cur in done:
            continue
        done.add(cur)
        visited.append(cur)
        if cur == goal:
            return build_path(parent, goal), visited
        for n in neighbors(obstacles, cur, rows, cols):
            ng = g[cur] + 1
            if ng < g.get(n, float("inf")):
                g[n] = ng
                parent[n] = cur
                count += 1
                heapq.heappush(heap, (ng + manhattan(n, goal), count, n))
    return None, visited


ALGORITHMS = {
    "BFS": bfs,
    "DFS": dfs,
    "Dijkstra": dijkstra,
    "A*": astar,
}
