#!/usr/bin/env python3
"""
Generate a "sim-to-real training run" SVG: a robot walks through your
GitHub contribution grid; each cell gets "trained" as the robot passes.
Output: animated SVG for profile README.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Try to fetch contribution data; fallback to placeholder grid
try:
    import urllib.request
    URLLIB_AVAILABLE = True
except ImportError:
    URLLIB_AVAILABLE = False

# GitHub contribution grid: 7 columns (Sun–Sat), 53 weeks
COLS, ROWS = 7, 53
CELL_SIZE = 10
GAP = 2
# GitHub-style contribution colors (light theme)
LEVEL_COLORS = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]
TRAINED_COLOR = "#1f77b4"   # "validated" cell
ROBOT_COLOR = "#333333"
PADDING = 24

WIDTH = COLS * (CELL_SIZE + GAP) - GAP + 2 * PADDING
HEIGHT = ROWS * (CELL_SIZE + GAP) - GAP + 2 * PADDING


def fetch_contribution_grid(username: str, token: str | None = None) -> list[list[int]]:
    """Fetch GitHub contribution data; return 2D grid [row][col] of levels 0–4."""
    grid = [[0] * COLS for _ in range(ROWS)]
    if not URLLIB_AVAILABLE:
        return _placeholder_grid()
    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "RobotTrainingSVG/1.0"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return _placeholder_grid()
    # Parse rects: data-date="2024-03-15" data-level="2" (and optionally x, y)
    # GitHub orders rects in the SVG; we need to map (date or position) -> (row, col)
    rects = re.findall(
        r'<rect[^>]*data-date="([^"]+)"[^>]*data-level="(\d)"[^>]*>',
        html,
    )
    if not rects:
        # Try data-count and infer level
        rects = re.findall(
            r'<rect[^>]*data-date="([^"]+)"[^>]*data-count="(\d+)"[^>]*>',
            html,
        )
    if not rects:
        return _placeholder_grid()
    from datetime import datetime
    # Build (date -> level) map
    date_to_level = {}
    for part in rects:
        if len(part) == 2:
            d, lev = part
            try:
                level = int(lev) if int(lev) <= 4 else 4
            except ValueError:
                level = min(4, int(lev) // 10) if lev.isdigit() else 0
            date_to_level[d] = level
    # GitHub graph: first column is Sunday, first row is oldest week. Order by date.
    sorted_dates = sorted(date_to_level.keys())
    if len(sorted_dates) < 10:
        return _placeholder_grid()
    for i, d in enumerate(sorted_dates):
        r, c = i // COLS, i % COLS
        if r < ROWS and c < COLS:
            grid[r][c] = date_to_level.get(d, 0)
    return grid


def _placeholder_grid() -> list[list[int]]:
    """Deterministic placeholder when fetch fails (e.g. in CI without token)."""
    grid = [[0] * COLS for _ in range(ROWS)]
    for r in range(ROWS):
        for c in range(COLS):
            grid[r][c] = (r * 7 + c) % 5
    return grid


def build_path() -> list[tuple[int, int]]:
    """Order cells so the robot walks through the grid (snake-style: left-right, then right-left)."""
    path = []
    for r in range(ROWS):
        if r % 2 == 0:
            for c in range(COLS):
                path.append((r, c))
        else:
            for c in range(COLS - 1, -1, -1):
                path.append((r, c))
    return path


def cell_xy(r: int, c: int) -> tuple[float, float]:
    x = PADDING + c * (CELL_SIZE + GAP)
    y = PADDING + r * (CELL_SIZE + GAP)
    return x, y


def emit_svg(grid: list[list[int]], path: list[tuple[int, int]], out_path: Path) -> None:
    total_cells = len(path)
    duration_per_cell = 0.10
    total_duration = total_cells * duration_per_cell

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
    ]

    # Grid cells
    for r in range(ROWS):
        for c in range(COLS):
            x, y = cell_xy(r, c)
            level = grid[r][c]
            color = LEVEL_COLORS[min(level, len(LEVEL_COLORS) - 1)]
            cell_id = f"c{r}_{c}"
            lines.append(f'  <rect id="{cell_id}" x="{x:.0f}" y="{y:.0f}" '
                        f'width="{CELL_SIZE}" height="{CELL_SIZE}" rx="2" ry="2" fill="{color}"/>')
    # Animate each cell to "trained" when robot passes
    for i, (r, c) in enumerate(path):
        cell_id = f"c{r}_{c}"
        base_color = LEVEL_COLORS[min(grid[r][c], len(LEVEL_COLORS) - 1)]
        t_begin = i * duration_per_cell
        lines.append(f'  <animate href="#{cell_id}" attributeName="fill" '
                    f'values="{base_color};{TRAINED_COLOR}" '
                    f'begin="{t_begin:.2f}s" dur="0.01s" fill="freeze"/>')

    # Robot (simple body + legs), centered at origin so animateMotion places it
    robot_w, robot_h = 10, 14
    lines.append('  <g id="robot">')
    lines.append(f'    <rect x="{-robot_w//2}" y="{-robot_h+4}" width="{robot_w}" height="{robot_h-4}" rx="2" fill="{ROBOT_COLOR}"/>')
    lines.append(f'    <rect x="{-robot_w//2+1}" y="0" width="{robot_w//2-1}" height="4" fill="{ROBOT_COLOR}"/>')
    lines.append(f'    <rect x="1" y="0" width="{robot_w//2-1}" height="4" fill="{ROBOT_COLOR}"/>')
    lines.append('  </g>')

    # Motion path: M cx,cy L cx,cy ... (center of each cell)
    path_points = []
    for r, c in path:
        x, y = cell_xy(r, c)
        path_points.append(f"{x + CELL_SIZE/2:.1f},{y + CELL_SIZE/2:.1f}")
    path_d = "M" + path_points[0] + " L" + " L".join(path_points[1:])
    lines.append(f'  <animateMotion href="#robot" dur="{total_duration}s" repeatCount="indefinite" path="{path_d}"/>')

    lines.append("</svg>")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    username = sys.argv[1] if len(sys.argv) > 1 else "ImmortalA"
    token = sys.argv[2] if len(sys.argv) > 2 else None
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(__file__).resolve().parent.parent / "assets" / "robot-training.svg"

    out.parent.mkdir(parents=True, exist_ok=True)
    grid = fetch_contribution_grid(username, token)
    path = build_path()
    emit_svg(grid, path, out)
    print(f"Wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
