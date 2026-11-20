"""길찾기 알고리즘 비교 게임 (패스파인더) - 클린 디자인 버전

실행:  pip install pygame  ->  python main.py
조작:  격자 클릭 = 장애물 설치/제거, 오른쪽 패널의 탭/버튼으로 알고리즘 선택·실행

(선택) Pretendard 폰트를 쓰려면 이 폴더에 fonts/Pretendard-Regular.ttf,
       fonts/Pretendard-Bold.ttf 를 넣으세요. 없으면 시스템 한글 폰트를 사용합니다.
"""
import os
import random
import time
from collections import deque

import pygame

from algorithms import ALGORITHMS

# ---------- 레이아웃 ----------
ROWS, COLS, CELL = 20, 20, 28
GX, GY = 40, 104                      # 격자 왼쪽 위
GRID_W, GRID_H = COLS * CELL, ROWS * CELL
WIN_W, WIN_H = 1280, 720
PX, PW = 660, 580                     # 오른쪽 패널 x, 너비

# ---------- 게임 설정 ----------
STEP_DELAY = 0.07                     # 기물 한 칸 이동 간격(초)
OBSTACLE_DENSITY = 0.22
START = (ROWS // 2, 0)
GOAL = (ROWS // 2, COLS - 1)

# ---------- 색 (포인트 색 하나 + 무채색) ----------
WHITE = (255, 255, 255)
INK = (17, 24, 39)
MUTED = (107, 114, 128)
LINE = (229, 231, 235)
HAIR = (243, 244, 246)
ACC = (37, 99, 235)
ACC_HOVER = (29, 78, 216)
WALL = (55, 65, 81)
GRID_BG = (250, 250, 250)
GRID_LINE = (238, 240, 243)

SORT_KEYS = [("탐색 노드", "nodes"), ("연산 시간", "compute_ms"), ("이동 칸수", "steps")]
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
SYSTEM_FONTS = ("pretendard", "malgungothic", "applegothic", "nanumgothic",
                "nanumbarungothic", "notosanscjkkr", "notosanscjk", "arialunicodems")


def load_font(size, bold=False):
    custom = os.path.join(FONT_DIR, "Pretendard-Bold.ttf" if bold else "Pretendard-Regular.ttf")
    if os.path.exists(custom):
        return pygame.font.Font(custom, size)
    for name in SYSTEM_FONTS:
        path = pygame.font.match_font(name)
        if path:
            f = pygame.font.Font(path, size)
            f.set_bold(bold)
            return f
    f = pygame.font.Font(None, size)
    f.set_bold(bold)
    return f


class Button:
    def __init__(self, rect, label, callback, primary=False):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.callback = callback
        self.primary = primary

    def draw(self, surf, font, mouse):
        hover = self.rect.collidepoint(mouse)
        if self.primary:
            pygame.draw.rect(surf, ACC_HOVER if hover else ACC, self.rect, border_radius=8)
            color = WHITE
        else:
            pygame.draw.rect(surf, (249, 250, 251) if hover else WHITE, self.rect, border_radius=8)
            pygame.draw.rect(surf, LINE, self.rect, 1, border_radius=8)
            color = INK
        txt = font.render(self.label, True, color)
        r = txt.get_rect()
        r.center = (self.rect.x + self.rect.w // 2, self.rect.y + self.rect.h // 2)
        surf.blit(txt, r)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("길찾기 알고리즘 비교 - 패스파인더")
        self.clock = pygame.time.Clock()
        self.f_title = load_font(20, True)
        self.f_big = load_font(60, True)
        self.f_unit = load_font(22)
        self.f_tab = load_font(16)
        self.f_tab_b = load_font(16, True)
        self.f_val = load_font(16, True)
        self.f_btn = load_font(14)
        self.f_row = load_font(14)
        self.f_row_b = load_font(14, True)
        self.f_sec = load_font(15, True)
        self.f_sm = load_font(13)
        self.f_xs = load_font(12)

        self.obstacles = set()
        self.selected = "BFS"
        self.sort_idx = 0
        self.ranking = deque(maxlen=12)   # 결과 큐
        self.message = "알고리즘을 고르고 [시작]을 누르세요 · 격자를 클릭하면 장애물을 놓을 수 있어요"
        self.reset_run()
        self.make_buttons()

    # ---------- 실행 상태 ----------
    def reset_run(self):
        self.pawn = START
        self.path = []
        self.visited = []
        self.running = False
        self.finished = False
        self.last_step = 0.0
        self.t_start = 0.0
        self.t_end = 0.0
        self.stats = dict(compute_ms=0.0, nodes=0, steps=0, replans=0)

    def plan(self, is_replan=False):
        algo = ALGORITHMS[self.selected]
        t0 = time.perf_counter()
        path, visited = algo(self.obstacles, self.pawn, GOAL, ROWS, COLS)
        dt = (time.perf_counter() - t0) * 1000
        self.stats["compute_ms"] += dt
        self.stats["nodes"] += len(visited)
        if is_replan:
            self.stats["replans"] += 1
        self.visited = visited
        if path is None:
            self.path = []
            self.finish(ok=False)
            return False
        self.path = path
        return True

    def start(self):
        if self.running:
            return
        self.reset_run()
        self.running = True
        self.t_start = time.perf_counter()
        self.last_step = time.perf_counter()
        self.message = f"{self.selected} 실행 중 · 격자를 클릭해 장애물을 놓아보세요"
        self.plan()

    def step(self):
        if len(self.path) > 1:
            self.path.pop(0)
            self.pawn = self.path[0]
            self.stats["steps"] += 1
        if self.pawn == GOAL:
            self.finish(ok=True)

    def finish(self, ok):
        self.running = False
        self.finished = True
        self.t_end = time.perf_counter()
        result = dict(name=self.selected, ok=ok,
                      total_s=self.t_end - self.t_start, **self.stats)
        self.ranking.append(result)
        self.message = "도착! 결과가 순위에 기록되었어요" if ok else "길이 막혀서 실패로 기록되었어요"

    # ---------- 맵 조작 ----------
    def random_map(self):
        if self.running:
            return
        self.reset_run()
        self.obstacles = {
            (r, c) for r in range(ROWS) for c in range(COLS)
            if random.random() < OBSTACLE_DENSITY
        } - {START, GOAL}
        self.message = "랜덤 맵 생성 · 같은 맵에서 알고리즘을 바꿔가며 비교해보세요"

    def clear_map(self):
        if self.running:
            return
        self.reset_run()
        self.obstacles.clear()
        self.message = "맵을 비웠어요"

    def reset_pawn(self):
        self.reset_run()
        self.message = "기물을 처음 위치로 돌렸어요 (맵은 유지)"

    def toggle_obstacle(self, cell):
        if cell in (START, GOAL, self.pawn):
            return
        if cell in self.obstacles:
            self.obstacles.remove(cell)
            return
        self.obstacles.add(cell)
        if self.running and cell in self.path:
            if self.plan(is_replan=True):
                self.message = f"경로가 막혀서 {self.selected}가 다시 탐색했어요"

    def throw_obstacle(self):
        """남은 경로 위에 장애물을 던져서 재탐색을 강제"""
        if not self.running or len(self.path) < 4:
            self.message = "경로 방해는 실행 중일 때만 사용할 수 있어요"
            return
        self.toggle_obstacle(random.choice(self.path[2:-1]))

    def cycle_sort(self):
        self.sort_idx = (self.sort_idx + 1) % len(SORT_KEYS)

    def reset_ranking(self):
        """순위 기록 초기화 (실행 중에는 무시)"""
        if self.running:
            return
        self.ranking.clear()
        self.message = "순위를 초기화했어요"

    def select(self, name):
        if not self.running:
            self.selected = name

    # ---------- 버튼 ----------
    def make_buttons(self):
        by = GY + 206
        self.tab_rects = [(name, pygame.Rect(PX + i * 110 - 6, GY + 20, 100, 38))
                          for i, name in enumerate(ALGORITHMS)]
        self.buttons = [Button((PX, by, 110, 40), "시작", self.start, primary=True)]
        for i, (label, cb) in enumerate([("기물 리셋", self.reset_pawn), ("랜덤 맵", self.random_map),
                                         ("맵 비우기", self.clear_map), ("경로 방해", self.throw_obstacle)]):
            self.buttons.append(Button((PX + 122 + i * 114, by, 106, 40), label, cb))
        self.sort_rect = pygame.Rect(PX + PW - 150, GY + 286, 150, 28)
        self.buttons.append(Button((PX + PW - 150 - 94, GY + 286, 86, 28),
                                   "순위 초기화", self.reset_ranking))

    # ---------- 그리기 도우미 ----------
    def text(self, s, x, y, color=INK, font=None, anchor="l"):
        surf = (font or self.f_row).render(s, True, color)
        r = surf.get_rect()
        if anchor == "r":
            r.topright = (x, y)
        elif anchor == "c":
            r.midtop = (x, y)
        else:
            r.topleft = (x, y)
        self.screen.blit(surf, r)

    def hline(self, y, x=PX, w=PW, color=LINE):
        pygame.draw.rect(self.screen, color, (x, y, w, 1))

    def elapsed(self):
        if self.running:
            return time.perf_counter() - self.t_start
        if self.finished:
            return self.t_end - self.t_start
        return 0.0

    # ---------- 그리기 ----------
    def draw_header(self):
        self.text("길찾기 알고리즘 비교", 40, 22, INK, self.f_title)
        self.text("같은 맵, 같은 장애물에서 알고리즘별 성능 측정", 226, 28, MUTED, self.f_sm)
        self.hline(72, 0, WIN_W)

    def draw_grid(self):
        pygame.draw.rect(self.screen, GRID_BG, (GX, GY, GRID_W, GRID_H))

        overlay = pygame.Surface((GRID_W, GRID_H), pygame.SRCALPHA)
        for r, c in self.visited:                     # 탐색 영역
            pygame.draw.rect(overlay, (*ACC, 18), (c * CELL, r * CELL, CELL, CELL))
        for r, c in self.path:                        # 투명한 예상 경로
            pygame.draw.rect(overlay, (*ACC, 100),
                             (c * CELL + 9, r * CELL + 9, CELL - 18, CELL - 18), border_radius=5)
        self.screen.blit(overlay, (GX, GY))

        for i in range(1, ROWS):
            pygame.draw.line(self.screen, GRID_LINE, (GX, GY + i * CELL), (GX + GRID_W, GY + i * CELL))
        for i in range(1, COLS):
            pygame.draw.line(self.screen, GRID_LINE, (GX + i * CELL, GY), (GX + i * CELL, GY + GRID_H))
        for r, c in self.obstacles:
            pygame.draw.rect(self.screen, WALL, (GX + c * CELL + 1, GY + r * CELL + 1, CELL - 2, CELL - 2))
        pygame.draw.rect(self.screen, LINE, (GX, GY, GRID_W, GRID_H), 1)

        def center(cell):
            return GX + cell[1] * CELL + CELL // 2, GY + cell[0] * CELL + CELL // 2

        sx, sy = center(START)                         # 출발: 속 빈 원
        pygame.draw.circle(self.screen, WHITE, (sx, sy), 9)
        pygame.draw.circle(self.screen, INK, (sx, sy), 9, 2)
        gx, gy = center(GOAL)                          # 도착: 검정 사각형
        pygame.draw.rect(self.screen, INK, (gx - 9, gy - 9, 18, 18), border_radius=3)
        px, py = center(self.pawn)                     # 기물: 파란 원
        pygame.draw.circle(self.screen, ACC, (px, py), 9)

    def draw_legend(self):
        y = GY + GRID_H + 12
        items = [("기물", "dot"), ("출발", "ring"), ("도착", "sq"), ("장애물", "wall"),
                 ("예상 경로", "path"), ("탐색 영역", "vis")]
        for i, (name, kind) in enumerate(items):
            x = GX + i * 92
            cx, cy = x + 5, y + 8
            if kind == "dot":
                pygame.draw.circle(self.screen, ACC, (cx, cy), 5)
            elif kind == "ring":
                pygame.draw.circle(self.screen, WHITE, (cx, cy), 5)
                pygame.draw.circle(self.screen, INK, (cx, cy), 5, 2)
            elif kind == "sq":
                pygame.draw.rect(self.screen, INK, (x, y + 3, 10, 10), border_radius=2)
            elif kind == "wall":
                pygame.draw.rect(self.screen, WALL, (x, y + 3, 10, 10))
            elif kind == "path":
                pygame.draw.rect(self.screen, (147, 175, 245), (x, y + 3, 10, 10), border_radius=2)
            else:
                pygame.draw.rect(self.screen, (222, 232, 252), (x, y + 3, 10, 10))
            self.text(name, x + 16, y + 1, MUTED, self.f_xs)

    def draw_panel(self, mouse):
        # 알고리즘 탭
        self.text("알고리즘", PX, GY, MUTED, self.f_xs)
        for i, (name, _) in enumerate(self.tab_rects):
            x = PX + i * 110
            sel = name == self.selected
            font = self.f_tab_b if sel else self.f_tab
            self.text(name, x, GY + 26, ACC if sel else MUTED, font)
            if sel:
                w = font.size(name)[0]
                pygame.draw.rect(self.screen, ACC, (x, GY + 50, w, 2))
        self.hline(GY + 60)

        # 타이머 + 지표
        self.text("경과 시간", PX, GY + 80, MUTED, self.f_xs)
        num = f"{self.elapsed():05.2f}"
        self.text(num, PX, GY + 98, INK, self.f_big)
        w = self.f_big.size(num)[0]
        self.text("초", PX + w + 8, GY + 134, MUTED, self.f_unit)
        s = self.stats
        stats = [("연산 시간", f"{s['compute_ms']:.2f} ms"), ("탐색 노드", f"{s['nodes']}"),
                 ("이동 칸수", f"{s['steps']}"), ("재탐색", f"{s['replans']}회")]
        for i, (k, v) in enumerate(stats):
            x = PX + 300 + (i % 2) * 140
            y = GY + 86 + (i // 2) * 44
            self.text(k, x, y, MUTED, self.f_xs)
            self.text(v, x, y + 16, INK, self.f_val)
        self.hline(GY + 186)

        # 버튼
        for b in self.buttons:
            b.draw(self.screen, self.f_btn, mouse)
        self.hline(GY + 270)

        # 순위 표
        self.text("순위", PX, GY + 288, INK, self.f_sec)
        hover = self.sort_rect.collidepoint(mouse)
        pygame.draw.rect(self.screen, (249, 250, 251) if hover else WHITE, self.sort_rect, border_radius=6)
        pygame.draw.rect(self.screen, LINE, self.sort_rect, 1, border_radius=6)
        label, key = SORT_KEYS[self.sort_idx]
        self.text(f"기준: {label}", self.sort_rect.x + 12, self.sort_rect.y + 6, INK, self.f_xs)
        ax, ay = self.sort_rect.right - 22, self.sort_rect.y + 12
        pygame.draw.lines(self.screen, MUTED, False, [(ax, ay), (ax + 5, ay + 5), (ax + 10, ay)], 2)

        hy = GY + 332
        cols = [("순위", PX, "l"), ("알고리즘", PX + 60, "l"), ("탐색 노드", PX + 300, "r"),
                ("연산 시간", PX + 400, "r"), ("이동", PX + 490, "r"), ("재탐색", PX + PW, "r")]
        for t, x, anc in cols:
            self.text(t, x, hy - 14, MUTED, self.f_xs, anc)
        self.hline(hy + 6)

        ok = sorted([r for r in self.ranking if r["ok"]], key=lambda r: r[key])
        fail = [r for r in self.ranking if not r["ok"]]
        rows = (ok + fail)[:5]
        for i, r in enumerate(rows):
            y = hy + 16 + i * 36
            top = i == 0 and r["ok"]
            color = ACC if top else (INK if r["ok"] else MUTED)
            font = self.f_row_b if top else self.f_row
            self.text(str(i + 1) if r["ok"] else "-", PX, y, color, font)
            name = r["name"] if r["ok"] else f"{r['name']} (실패)"
            self.text(name, PX + 60, y, color, font)
            self.text(str(r["nodes"]), PX + 300, y, color, font, "r")
            self.text(f"{r['compute_ms']:.2f} ms", PX + 400, y, color, font, "r")
            self.text(str(r["steps"]), PX + 490, y, color, font, "r")
            self.text(str(r["replans"]), PX + PW, y, color, font, "r")
            self.hline(y + 24, color=HAIR)

        self.text(self.message, PX, GY + GRID_H + 12, MUTED, self.f_sm)

    # ---------- 메인 루프 ----------
    def handle_click(self, pos):
        for name, rect in self.tab_rects:
            if rect.collidepoint(pos):
                self.select(name)
                return
        for b in self.buttons:
            if b.rect.collidepoint(pos):
                b.callback()
                return
        if self.sort_rect.collidepoint(pos):
            self.cycle_sort()
            return
        gx, gy = pos[0] - GX, pos[1] - GY
        if 0 <= gx < GRID_W and 0 <= gy < GRID_H:
            self.toggle_obstacle((gy // CELL, gx // CELL))

    def run(self):
        while True:
            mouse = pygame.mouse.get_pos()
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    return
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    self.handle_click(e.pos)

            if self.running and time.perf_counter() - self.last_step >= STEP_DELAY:
                self.last_step = time.perf_counter()
                self.step()

            self.screen.fill(WHITE)
            self.draw_header()
            self.draw_grid()
            self.draw_legend()
            self.draw_panel(mouse)
            pygame.display.flip()
            self.clock.tick(60)


if __name__ == "__main__":
    Game().run()
