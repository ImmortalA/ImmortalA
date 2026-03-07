#!/usr/bin/env python3
"""
Generate a simple SVG: humanoid figure walking left-to-right and back.
Small, clean animation for profile README.
"""
from pathlib import Path
import sys

# Short horizontal strip: wide and low so it doesn’t look like a vertical block
WIDTH = 200
HEIGHT = 26
# Humanoid size (fits in HEIGHT)
HEAD_R = 3
BODY_W, BODY_H = 4, 8
LEG_W, LEG_H = 2, 4
# Path: left -> right -> left (Y so humanoid fits in viewBox)
PATH_MARGIN = 20
PATH_Y = 20  # feet at y=20, head ~y=6


def emit_svg(out_path: Path) -> None:
    # Motion path: go right then back (M start, L end, L end, L start for round-trip)
    path_d = f"M{PATH_MARGIN},{PATH_Y} L{WIDTH - PATH_MARGIN},{PATH_Y} L{WIDTH - PATH_MARGIN},{PATH_Y} L{PATH_MARGIN},{PATH_Y}"
    duration = "3s"

    cy_head = -BODY_H - HEAD_R
    left_leg_x = -BODY_W // 2
    right_leg_x = BODY_W // 2 - LEG_W

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        '  <g id="humanoid">',
        f'    <circle cx="0" cy="{cy_head}" r="{HEAD_R}" fill="#333"/>',
        f'    <rect x="-{BODY_W//2}" y="-{BODY_H}" width="{BODY_W}" height="{BODY_H}" rx="1" fill="#333"/>',
        f'    <rect x="{left_leg_x}" y="0" width="{LEG_W}" height="{LEG_H}" rx="1" fill="#333"/>',
        f'    <rect x="{right_leg_x}" y="0" width="{LEG_W}" height="{LEG_H}" rx="1" fill="#333"/>',
        '  </g>',
        f'  <animateMotion href="#humanoid" dur="{duration}" repeatCount="indefinite" path="{path_d}"/>',
        '</svg>',
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(__file__).resolve().parent.parent / "assets" / "robot-training.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    emit_svg(out)
    print(f"Wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
