#!/usr/bin/env python3
"""Generate README image assets for dsh-demurrage-ledger (docs/assets/).

Outputs (idempotent overwrite):
  dsh-demurrage-ledger-flow-light.svg / dsh-demurrage-ledger-flow-dark.svg
      Hero flow diagram: material -> demurrage_ledger -> columns -> rule pack
      -> report. Two hand-written SVG files (vector — never rasterized to
      webp). Text inside is command-surface tokens only (tool name, rule ids,
      JSON/YAML), so all five README languages share the same pair.
  No WebP asset: this repo has no UI screenshots and no benchmark data, so
  there is no evidence chart to draw. WEBP_QUALITY is kept for family parity
  with the other PerryLink generators.

Run once:  python scripts/gen-readme-assets.py
Requires:  Pillow (only for the font probe today; bundled runtime has it)
"""
from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw, ImageFont  # noqa: F401  (family skeleton)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "assets")

# --- palette: PerryLink family (accent) + GitHub page backgrounds ----------
FAMILY = "#4B67B4"   # family accent (badges labelColor family uses #2B3245)
GREEN = {"light": "#16a34a", "dark": "#3fb950"}
SKIN = {
    "light": dict(bg="#ffffff", box="#f6f8fa", border="#d0d7de",
                  text="#1f2328", sub="#57606a"),
    "dark": dict(bg="#0d1117", box="#161b22", border="#30363d",
                 text="#f0f6fc", sub="#8b949e"),
}
WEBP_QUALITY = 90

# --- CJK font probe: Chinese must never render as tofu boxes ----------------
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",      # Microsoft YaHei
    r"C:\Windows\Fonts\simhei.ttf",    # SimHei
    r"C:\Windows\Fonts\Deng.ttf",      # DengXian
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/PingFang.ttc",
]
FONT_PATH = next((p for p in FONT_CANDIDATES if os.path.exists(p)), None)


def require_cjk_font() -> None:
    """Abort loudly when no CJK font is installed.

    Today's SVG carries ASCII tokens only, but the family generator refuses
    to run on a machine where a future Pillow-rendered asset (an evidence
    chart) would silently render Chinese as tofu boxes.
    """
    if FONT_PATH is None:
        sys.exit("FATAL: no CJK font found (looked for msyh.ttc, simhei.ttf, "
                 "Deng.ttf, Noto Sans CJK, PingFang). Refusing to render "
                 "Chinese as tofu boxes; install one of the probed fonts and "
                 "re-run.")


# ---------------------------------------------------------------------------
# Hero flow SVG (light + dark)
# ---------------------------------------------------------------------------
FLOW_NODES = [
    ("material", "JSON | YAML"),
    ("demurrage_ledger", "file | material"),
    ("parseTable", "containerNo | blNo"),
    ("rules/*.yaml", "DL-001 … DL-007"),
    ("report", "issues + skipped"),
]


def flow_svg(skin: str) -> str:
    s = SKIN[skin]
    w, h = 1200, 400
    nw, nh, gap = 180, 96, 45
    y0 = 150
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" '
        f'aria-label="dsh-demurrage-ledger flow">',
        '<title>dsh-demurrage-ledger flow</title>',
        f'<rect width="{w}" height="{h}" rx="18" fill="{s["bg"]}"/>',
        f'<text x="60" y="62" fill="{s["text"]}" font-family="ui-sans-serif,'
        f'system-ui,sans-serif" font-size="30" font-weight="700">'
        f'dsh-demurrage-ledger</text>',
        f'<text x="60" y="94" fill="{s["sub"]}" font-family="ui-monospace,'
        f'monospace" font-size="16">material -&gt; rule pack -&gt; report; '
        f'no network, no model call, no writes</text>',
        f'<line x1="60" y1="116" x2="1140" y2="116" stroke="{s["border"]}"/>',
    ]
    for i, (label, sub) in enumerate(FLOW_NODES):
        x = 60 + i * (nw + gap)
        accent = GREEN[skin] if i == len(FLOW_NODES) - 1 else (
            FAMILY if i == 1 else s["border"])
        parts.append(
            f'<rect x="{x}" y="{y0}" width="{nw}" height="{nh}" rx="14" '
            f'fill="{s["box"]}" stroke="{accent}" stroke-width="2"/>')
        parts.append(
            f'<text x="{x + nw // 2}" y="{y0 + 40}" fill="{s["text"]}" '
            f'text-anchor="middle" font-family="ui-monospace,monospace" '
            f'font-size="16" font-weight="700">{label}</text>')
        parts.append(
            f'<text x="{x + nw // 2}" y="{y0 + 68}" fill="{s["sub"]}" '
            f'text-anchor="middle" font-family="ui-monospace,monospace" '
            f'font-size="12">{sub}</text>')
        if i < len(FLOW_NODES) - 1:
            ax = x + nw + 6
            ay = y0 + nh // 2
            parts.append(
                f'<path d="M{ax} {ay}h{gap - 12}" stroke="{s["sub"]}" '
                f'stroke-width="3"/>')
            parts.append(
                f'<path d="M{ax + gap - 14} {ay - 7}l10 7-10 7" fill="none" '
                f'stroke="{s["sub"]}" stroke-width="3" '
                f'stroke-linecap="round" stroke-linejoin="round"/>')
    # skipped bar under the tool/rule nodes: a check that cannot run is named
    bx, bw, by, bh = 285, 630, 285, 52
    for cx in (285 + 90, 735 + 90):  # node2 / node4 centres
        parts.append(
            f'<path d="M{cx} {y0 + nh}v{by - y0 - nh}" '
            f'stroke="{FAMILY}" stroke-width="2" stroke-dasharray="5 5"/>')
    parts.append(
        f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="12" '
        f'fill="{s["box"]}" stroke="{FAMILY}" stroke-width="2"/>')
    parts.append(
        f'<text x="{bx + bw // 2}" y="{by + 33}" fill="{s["text"]}" '
        f'text-anchor="middle" font-family="ui-monospace,monospace" '
        f'font-size="14">skipped[] · rule id + reason · never silent</text>')
    parts.append(
        f'<text x="60" y="378" fill="{s["sub"]}" font-family="ui-monospace,'
        f'monospace" font-size="13">network: none · writes: none · '
        f'model calls: none · Apache-2.0</text>')
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def main() -> None:
    require_cjk_font()
    os.makedirs(OUT, exist_ok=True)
    for skin in ("light", "dark"):
        path = os.path.join(OUT, f"dsh-demurrage-ledger-flow-{skin}.svg")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(flow_svg(skin))
    print("wrote 2 SVG assets to docs/assets/ (no WebP: no UI, no benchmark)")


if __name__ == "__main__":
    main()
