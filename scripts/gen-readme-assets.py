#!/usr/bin/env python3
"""README visuals for dsh-demurrage-ledger (docs/assets/).

Two figures, both derived from the shipped rule pack and the shipped contract,
never from an imagined feature:

1. Hero banner, 1440x576, Pillow, four files (zh/en x light/dark).
   Left column: kicker, wordmark, two value lines, one subtitle, one meta
   line, footer. Right side: the plugin's own semantic object, a ledger row
   fragment -> the DL-003 arithmetic -> one located issue card. The numbers
   are consistent with each other (7 free days, 14 calendar days, 7 derived
   overdue days, filed 10, rate 126, amount 1,260) and with the rule pack.

2. Structure figure, 1100x660, hand-written SVG, two files (light/dark),
   shared by all five README languages because it is token-only.
   Grammar: an incidence MATRIX, ledger field (10 rows) x rule (7 columns).
   A cell means "this rule reads this field": filled dot = the field the
   issue is located on (locator.field), ring = a field the rule compares
   against. Nothing else in the pack is read. The matrix is the real data
   model: seven `kind` checks over ten canonical columns.

Run:  python scripts/gen-readme-assets.py
Fonts: msyh.ttc / msyhbd.ttc (Chinese), consola.ttf (mono), segoeui*.ttf
       (English prose). All are probed; the script refuses to render tofu.
"""
from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from html import escape

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "assets")

FONT_CJK = r"C:\Windows\Fonts\msyh.ttc"
FONT_CJK_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_MONO = r"C:\Windows\Fonts\consola.ttf"
FONT_MONO_BOLD = r"C:\Windows\Fonts\consolab.ttf"
FONT_EN = r"C:\Windows\Fonts\segoeui.ttf"
FONT_EN_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
for _path in (FONT_CJK, FONT_CJK_BOLD, FONT_MONO, FONT_EN, FONT_EN_BOLD):
    if not os.path.exists(_path):
        raise SystemExit(f"FATAL: font missing: {_path}")
if not os.path.exists(FONT_MONO_BOLD):
    FONT_MONO_BOLD = FONT_MONO

SKIN = {
    "light": dict(
        bg_from="#f9f6fd", bg_to="#e4eaf8",
        card="#ffffff", edge="#e4e1ee",
        text="#141419", sub="#4d5261", faint="#8f94a4",
        accent="#4B67B4", accent2="#16a34a", warn="#bc4c00",
        pill="#ece7f9", grid="#e7e4f0",
        shadow=(32, 26, 64), dot_alpha=14, glow_alpha=34,
    ),
    "dark": dict(
        bg_from="#131a2a", bg_to="#0c1016",
        card="#1b2231", edge="#2e374b",
        text="#f0f3f9", sub="#a8b1c4", faint="#737b8d",
        accent="#8496f5", accent2="#3fb950", warn="#d29922",
        pill="#242d42", grid="#2a3346",
        shadow=(0, 0, 0), dot_alpha=26, glow_alpha=52,
    ),
}

WEBP_QUALITY = 92

# --------------------------------------------------------------------------- #
# drawing helpers
# --------------------------------------------------------------------------- #


def hx(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def mix(color: str, base: str, amount: float) -> tuple[int, int, int]:
    """Blend `color` over `base` by `amount` (0..1) for flat RGB drawing."""
    top, under = hx(color), hx(base)
    return tuple(int(top[i] * amount + under[i] * (1 - amount)) for i in range(3))


def font(size: float, kind: str = "cjk") -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(
        {
            "cjk": FONT_CJK,
            "cjk_bold": FONT_CJK_BOLD,
            "mono": FONT_MONO,
            "mono_bold": FONT_MONO_BOLD,
            "en": FONT_EN,
            "en_bold": FONT_EN_BOLD,
        }[kind],
        int(round(size)),
    )


def gradient(w: int, h: int, top: str, bottom: str) -> Image.Image:
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    c1, c2 = hx(top), hx(bottom)
    for y in range(h):
        t = 0.25 * (y / h) + 0.75 * (y / h) ** 1.35
        draw.line([(0, y), (w, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(c1, c2)))
    return img


def add_glow(img: Image.Image, cx: float, cy: float, radius: float,
             color: str, alpha: int) -> Image.Image:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        fill=hx(color) + (alpha,),
    )
    layer = layer.filter(ImageFilter.GaussianBlur(radius * 0.55))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def add_dots(img: Image.Image, color: str, alpha: int, step: int = 26) -> Image.Image:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    dot = hx(color) + (alpha,)
    for y in range(step // 2, img.height, step):
        for x in range(step // 2, img.width, step):
            draw.ellipse([x - 1.1, y - 1.1, x + 1.1, y + 1.1], fill=dot)
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def soft_card(img: Image.Image, box: tuple[int, int, int, int], skin: dict,
              radius: int = 18, shadow: int = 22) -> Image.Image:
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for i in range(shadow, 0, -4):
        draw.rounded_rectangle(
            [x0 - i // 5, y0 + i // 2, x1 + i // 5, y1 + i],
            radius=radius + i // 4,
            fill=skin["shadow"] + (int(9 * (1 - i / shadow)),),
        )
    layer = layer.filter(ImageFilter.GaussianBlur(13))
    base = Image.alpha_composite(img.convert("RGBA"), layer)
    ImageDraw.Draw(base).rounded_rectangle(
        box, radius=radius, fill=hx(skin["card"]), outline=hx(skin["edge"]), width=2)
    return base.convert("RGB")


def text_width(draw: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont) -> float:
    return draw.textlength(text, font=f)


def fits(draw: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont,
         limit: float, label: str) -> float:
    width = text_width(draw, text, f)
    if width > limit:
        raise SystemExit(f"FATAL: {label} overflows: {width:.1f} > {limit:.0f} px ({text!r})")
    return width


def pill(img: Image.Image, xy: tuple[int, int], text: str, skin: dict,
         size: float = 17, kind: str = "cjk_bold", dot: bool = False) -> None:
    draw = ImageDraw.Draw(img)
    f = font(size, kind)
    width = text_width(draw, text, f)
    height = int(size) + 19
    x, y = xy
    box_w = int(width) + 34 + (14 if dot else 0)
    draw.rounded_rectangle([x, y, x + box_w, y + height], radius=height // 2,
                           fill=hx(skin["pill"]))
    if dot:
        cy = y + height // 2
        draw.ellipse([x + 15, cy - 3.5, x + 22, cy + 3.5], fill=hx(skin["accent"]))
    draw.text((x + (29 if dot else 17), y + height // 2), text, font=f,
              fill=hx(skin["accent"]), anchor="lm")


# --------------------------------------------------------------------------- #
# hero: 1440x576
# --------------------------------------------------------------------------- #

HERO = {
    "zh": dict(
        kicker="DeepSeek Harness 插件 · 滞箱费台账核查",
        value=("把说不通的数字逐行指出来", "只列差异，不替你定性"),
        sub="读表头加每箱一行，核对齐备与算术；只读、不联网、不改原件。",
        meta="JSON / YAML · 7 条规则 · issues + skipped · 不联网 · 不写盘",
        foot="Apache-2.0 · PerryLink DSH plugin family · rules/demurrage-ledger.yaml",
        headers=("箱号", "超期天数", "费率", "金额"),
        rows=(("MSCU1234567", "7", "126", "882"),
              ("TGHU7654321", "10", "126", "1,260")),
        eq_left="returnAt − startAt − freeDays",
        eq_mid="= 7",
        eq_right="≠  overdueDays 10",
        issue=("DL-003 · warn",
               "locator: row 2 · overdueDays",
               "found 10 · expected 7",
               "建议核对：按两个日期与免箱期复算"),
        tags=("input", "tolerance 0", "issues[0]"),
    ),
    "en": dict(
        kicker="DeepSeek Harness plugin · demurrage ledger check",
        value=("Point out the numbers that do not add up", "row by row, field by field"),
        sub="Header + one row per container in; differences out, never a verdict.",
        meta="JSON / YAML · 7 rules DL-001…DL-007 · issues + skipped · no network",
        foot="Apache-2.0 · PerryLink DSH plugin family · rules/demurrage-ledger.yaml",
        headers=("container", "overdue days", "rate", "amount"),
        rows=(("MSCU1234567", "7", "126", "882"),
              ("TGHU7654321", "10", "126", "1,260")),
        eq_left="returnAt − startAt − freeDays",
        eq_mid="= 7",
        eq_right="≠  overdueDays 10",
        issue=("DL-003 · warn",
               "locator: row 2 · overdueDays",
               "found 10 · expected 7",
               "fix: recompute from the dates + freeDays"),
        tags=("input", "tolerance 0", "issues[0]"),
    ),
}


def hero(lang: str, skin_name: str) -> str:
    s = SKIN[skin_name]
    h = HERO[lang]
    w, height = 1440, 576
    img = gradient(w, height, s["bg_from"], s["bg_to"])
    img = add_glow(img, 1220, 44, 430, s["accent"], s["glow_alpha"])
    img = add_glow(img, 150, 570, 330, s["accent"], s["glow_alpha"] // 2)
    img = add_dots(img, s["accent"], s["dot_alpha"])
    draw = ImageDraw.Draw(img)

    # --- left column -------------------------------------------------------
    pill(img, (48, 40), h["kicker"], s, size=18, dot=True)
    draw = ImageDraw.Draw(img)

    title_font = font(80, "mono")
    fits(draw, "dsh-demurrage-ledger", title_font, 900, "hero title")
    draw.text((48, 176), "dsh-demurrage-ledger", font=title_font,
              fill=hx(s["text"]), anchor="ls")
    draw.rounded_rectangle([48, 194, 122, 199], radius=3, fill=hx(s["accent"]))

    value_font = font(44 if lang == "zh" else 40, "cjk_bold" if lang == "zh" else "en_bold")
    fits(draw, h["value"][0], value_font, 880, "hero value 1")
    fits(draw, h["value"][1], value_font, 880, "hero value 2")
    draw.text((48, 258), h["value"][0], font=value_font, fill=hx(s["text"]), anchor="ls")
    draw.text((48, 318), h["value"][1], font=value_font, fill=hx(s["accent"]), anchor="ls")

    sub_font = font(26 if lang == "zh" else 25, "cjk" if lang == "zh" else "en")
    fits(draw, h["sub"], sub_font, 880, "hero subtitle")
    draw.text((48, 374), h["sub"], font=sub_font, fill=hx(s["sub"]), anchor="ls")

    meta_font = font(21, "cjk" if lang == "zh" else "mono")
    fits(draw, h["meta"], meta_font, 880, "hero meta")
    draw.text((48, 414), h["meta"], font=meta_font, fill=hx(s["faint"]), anchor="ls")

    draw.line([48, 466, 640, 466], fill=hx(s["grid"]), width=2)
    foot_font = font(18, "mono")
    fits(draw, h["foot"], foot_font, 880, "hero footer")
    draw.text((48, 500), h["foot"], font=foot_font, fill=hx(s["faint"]), anchor="ls")

    # --- right visual: ledger row -> arithmetic -> located issue ------------
    left, right = 952, 1392
    inner_left = left + 24

    # A. ledger row fragment
    img = soft_card(img, (left, 58, right, 236), s)
    draw = ImageDraw.Draw(img)
    draw.text((inner_left, 84), "rows[2]", font=font(15, "mono"),
              fill=hx(s["accent"]), anchor="ls")
    draw.text((right - 24, 84), h["tags"][0], font=font(15, "mono"),
              fill=hx(s["faint"]), anchor="rs")
    col_x = (inner_left, 1096, 1200, 1288)
    head_font = font(15, "cjk" if lang == "zh" else "en")
    for x, label in zip(col_x, h["headers"]):
        draw.text((x, 120), label, font=head_font, fill=hx(s["faint"]), anchor="ls")
    draw.line([inner_left, 130, right - 24, 130], fill=hx(s["grid"]), width=2)

    value_font = font(17, "mono")
    for index, row in enumerate(h["rows"]):
        y = 162 if index == 0 else 200
        if index == 1:
            draw.rounded_rectangle([960, 176, right - 8, 216], radius=12,
                                   fill=mix(s["warn"], s["card"], 0.10))
        for column, (x, cell) in enumerate(zip(col_x, row)):
            color = s["warn"] if (index == 1 and column == 1) else s["text"]
            draw.text((x, y), cell, font=value_font, fill=hx(color), anchor="ls")

    # B. the DL-003 arithmetic
    img = soft_card(img, (left, 254, right, 372), s)
    draw = ImageDraw.Draw(img)
    draw.text((inner_left, 280), "DL-003 · arithmetic", font=font(15, "mono"),
              fill=hx(s["accent"]), anchor="ls")
    draw.text((right - 24, 280), h["tags"][1], font=font(15, "mono"),
              fill=hx(s["faint"]), anchor="rs")
    eq_font = font(19, "mono")
    fits(draw, h["eq_left"], eq_font, right - 24 - inner_left, "hero equation 1")
    draw.text((inner_left, 314), h["eq_left"], font=eq_font,
              fill=hx(s["sub"]), anchor="ls")
    draw.text((inner_left, 344), h["eq_mid"], font=eq_font,
              fill=hx(s["sub"]), anchor="ls")
    offset = inner_left + text_width(draw, h["eq_mid"] + "   ", eq_font)
    draw.text((offset, 344), h["eq_right"], font=eq_font,
              fill=hx(s["warn"]), anchor="ls")

    # C. one located issue
    img = soft_card(img, (left, 390, right, 526), s)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([left, 390, left + 6, 526], radius=3, fill=hx(s["accent"]))
    draw.text((inner_left, 416), h["tags"][2], font=font(15, "mono"),
              fill=hx(s["accent"]), anchor="ls")
    draw.text((inner_left, 448), h["issue"][0], font=font(17.5, "mono_bold"),
              fill=hx(s["warn"]), anchor="ls")
    draw.text((inner_left, 474), h["issue"][1], font=font(16, "mono"),
              fill=hx(s["sub"]), anchor="ls")
    draw.text((inner_left, 496), h["issue"][2], font=font(16, "mono"),
              fill=hx(s["sub"]), anchor="ls")
    issue_font = font(16 if lang == "zh" else 15, "cjk" if lang == "zh" else "mono")
    fits(draw, h["issue"][3], issue_font, right - 24 - inner_left, "hero issue fix")
    draw.text((inner_left, 516), h["issue"][3], font=issue_font,
              fill=hx(s["faint"]), anchor="ls")

    name = f"dsh-demurrage-ledger-hero-{lang}-{skin_name}.webp"
    img.save(os.path.join(OUT, name), "WEBP", quality=WEBP_QUALITY, method=6)
    return name


# --------------------------------------------------------------------------- #
# structure figure: 1100x660, incidence matrix
# --------------------------------------------------------------------------- #

RULES = [
    ("DL-001", "presenceAny"),
    ("DL-002", "date"),
    ("DL-003", "derivedDays"),
    ("DL-004", "productOf"),
    ("DL-005", "pattern"),
    ("DL-006", "unique"),
    ("DL-007", "containsAny"),
]

# field -> {rule id: "solid" | "ring"}; direct reading of
# rules/demurrage-ledger.yaml params (field / fields / resultField /
# daysField / fromField / toField / subtractField / factorFields).
FIELDS = [
    ("containerNo", {"DL-001": "solid", "DL-006": "solid"}),
    ("blNo", {"DL-001": "ring"}),
    ("freeDays", {"DL-003": "ring"}),
    ("startAt", {"DL-002": "solid", "DL-003": "ring"}),
    ("returnAt", {"DL-002": "ring", "DL-003": "ring"}),
    ("overdueDays", {"DL-003": "solid", "DL-004": "ring"}),
    ("rate", {"DL-004": "ring"}),
    ("amount", {"DL-004": "solid"}),
    ("currency", {"DL-005": "solid"}),
    ("note", {"DL-007": "solid"}),
]

SVG_SKIN = {
    "light": dict(
        bg_from="#f9f6fd", bg_to="#e4eaf8",
        card="#ffffff", edge="#e4e1ee",
        text="#141419", sub="#4d5261", faint="#8f94a4",
        accent="#4B67B4", warn="#bc4c00", grid="#e8e4f1",
        pill="#efeaf9", dot="#cfc8e2", shadow="#2b2440", shadow_opacity="0.13",
    ),
    "dark": dict(
        bg_from="#131a2a", bg_to="#0c1016",
        card="#1b2231", edge="#2e374b",
        text="#f0f3f9", sub="#a8b1c4", faint="#7c8598",
        accent="#8496f5", warn="#d29922", grid="#262f42",
        pill="#242d42", dot="#39445c", shadow="#000000", shadow_opacity="0.55",
    ),
}

W, H = 1100, 660
CARD = (40, 112, 1060, 598)
LABEL_X = 64
MATRIX_X = 326
COL_W = (CARD[2] - 24 - MATRIX_X) / len(RULES)  # 101.43
ROW_Y0, ROW_H = 200, 34


def rule_center(index: int) -> float:
    return MATRIX_X + COL_W * (index + 0.5)


def probe_width(text: str, size: float, kind: str) -> float:
    image = Image.new("RGB", (8, 8))
    draw = ImageDraw.Draw(image)
    return draw.textlength(text, font=font(size, kind))


def svg_flow(skin_name: str) -> str:
    s = SVG_SKIN[skin_name]
    sans = "'Segoe UI', 'Microsoft YaHei', system-ui, sans-serif"
    mono = "Consolas, 'Courier New', monospace"

    def tw(text: str, size: float) -> float:
        return probe_width(text, size, "mono")

    def check(text: str, size: float, limit: float, label: str) -> None:
        width = tw(text, size)
        if width > limit:
            raise SystemExit(f"FATAL: svg {label} overflows: {width:.1f} > {limit:.0f} ({text!r})")

    parts: list[str] = []
    add = parts.append
    add(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">
<title id="title">dsh-demurrage-ledger field x rule incidence matrix</title>
<desc id="desc">Ten ledger fields as rows, seven rule ids as columns. A filled dot marks the field a finding is located on; a ring marks a field the rule compares against. Every rule is severity warn; a check that cannot run is reported in skipped.</desc>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{s['bg_from']}"/>
    <stop offset="1" stop-color="{s['bg_to']}"/>
  </linearGradient>
  <filter id="soft" x="-30%" y="-30%" width="160%" height="180%">
    <feDropShadow dx="0" dy="10" stdDeviation="14" flood-color="{s['shadow']}" flood-opacity="{s['shadow_opacity']}"/>
  </filter>
  <pattern id="dots" width="26" height="26" patternUnits="userSpaceOnUse">
    <circle cx="1.2" cy="1.2" r="1.2" fill="{s['dot']}"/>
  </pattern>
</defs>
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<rect width="{W}" height="{H}" fill="url(#dots)" opacity=".55"/>''')

    # --- masthead ----------------------------------------------------------
    add(f'<text x="44" y="54" fill="{s["text"]}" font-family="{mono}" '
        f'font-size="34" font-weight="700">dsh-demurrage-ledger</text>')
    subtitle = "field × rule incidence matrix: every cell the seven rules read"
    add(f'<text x="44" y="84" fill="{s["sub"]}" font-family="{sans}" '
        f'font-size="15.5">{escape(subtitle)}</text>')

    for index, (label, y0) in enumerate((("in · JSON | YAML", 34),
                                        ("out · issues[] + skipped[]", 70))):
        width = tw(label, 14) + 30
        x0 = 1056 - width
        add(f'<rect x="{x0:.1f}" y="{y0}" width="{width:.1f}" height="30" rx="15" '
            f'fill="{s["pill"]}"/>')
        add(f'<text x="{x0 + 15:.1f}" y="{y0 + 20}" fill="{s["accent"]}" '
            f'font-family="{mono}" font-size="14">{escape(label)}</text>')

    # --- matrix card -------------------------------------------------------
    add(f'<g filter="url(#soft)"><rect x="{CARD[0]}" y="{CARD[1]}" '
        f'width="{CARD[2] - CARD[0]}" height="{CARD[3] - CARD[1]}" rx="20" '
        f'fill="{s["card"]}" stroke="{s["edge"]}"/></g>')

    add(f'<text x="{LABEL_X}" y="158" fill="{s["accent"]}" font-family="{sans}" '
        f'font-size="14" font-weight="700" letter-spacing="1.5">LEDGER FIELD</text>')
    add(f'<text x="{LABEL_X}" y="182" fill="{s["faint"]}" font-family="{mono}" '
        f'font-size="14">10 columns read</text>')

    for index, (rule_id, kind) in enumerate(RULES):
        cx = rule_center(index)
        add(f'<rect x="{cx - 37:.1f}" y="136" width="74" height="32" rx="10" '
            f'fill="{s["accent"]}" fill-opacity=".10" '
            f'stroke="{s["accent"]}" stroke-opacity=".30"/>')
        add(f'<text x="{cx:.1f}" y="158" text-anchor="middle" fill="{s["accent"]}" '
            f'font-family="{mono}" font-size="16.5" font-weight="700">{rule_id}</text>')
        check(kind, 14, COL_W - 8, f"kind {rule_id}")
        add(f'<text x="{cx:.1f}" y="182" text-anchor="middle" fill="{s["sub"]}" '
            f'font-family="{mono}" font-size="14">{escape(kind)}</text>')

    add(f'<line x1="{LABEL_X}" y1="192" x2="{CARD[2] - 24}" y2="192" '
        f'stroke="{s["grid"]}" stroke-width="2"/>')
    add(f'<line x1="{MATRIX_X}" y1="{ROW_Y0}" x2="{MATRIX_X}" y2="540" '
        f'stroke="{s["grid"]}" stroke-width="1.5"/>')
    for index in range(1, len(RULES)):
        x = MATRIX_X + COL_W * index
        add(f'<line x1="{x:.1f}" y1="{ROW_Y0}" x2="{x:.1f}" y2="540" '
            f'stroke="{s["grid"]}" stroke-width="1" stroke-opacity=".95"/>')
    for index in range(1, len(FIELDS)):
        y = ROW_Y0 + ROW_H * index
        add(f'<line x1="{LABEL_X}" y1="{y}" x2="{CARD[2] - 24}" y2="{y}" '
            f'stroke="{s["grid"]}" stroke-width="1" stroke-opacity=".75"/>')
    add(f'<line x1="{LABEL_X}" y1="540" x2="{CARD[2] - 24}" y2="540" '
        f'stroke="{s["grid"]}" stroke-width="1.5"/>')

    # --- rows --------------------------------------------------------------
    field_font = 17.5
    for index, (field_name, marks) in enumerate(FIELDS):
        cy = ROW_Y0 + ROW_H * index + ROW_H / 2
        check(field_name, field_font, MATRIX_X - LABEL_X - 40, f"field {field_name}")
        add(f'<text x="{LABEL_X}" y="{cy + 5:.1f}" fill="{s["faint"]}" '
            f'font-family="{mono}" font-size="14">{index + 1:02d}</text>')
        add(f'<text x="96" y="{cy + 6:.1f}" fill="{s["text"]}" font-family="{mono}" '
            f'font-size="{field_font}" font-weight="700">{escape(field_name)}</text>')
        for column, (rule_id, _kind) in enumerate(RULES):
            cx = rule_center(column)
            mark = marks.get(rule_id)
            if mark is None:
                continue
            if mark == "solid":
                add(f'<rect x="{cx - 13:.1f}" y="{cy - 13:.1f}" width="26" height="26" '
                    f'rx="8" fill="{s["accent"]}" fill-opacity=".13" '
                    f'stroke="{s["accent"]}" stroke-opacity=".38"/>')
                add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5.2" fill="{s["accent"]}"/>')
            else:
                add(f'<rect x="{cx - 13:.1f}" y="{cy - 13:.1f}" width="26" height="26" '
                    f'rx="8" fill="none" stroke="{s["accent"]}" stroke-opacity=".22"/>')
                add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.8" fill="none" '
                    f'stroke="{s["accent"]}" stroke-width="1.6"/>')

    # --- legend and outcomes ----------------------------------------------
    add(f'<line x1="{LABEL_X}" y1="548" x2="{CARD[2] - 24}" y2="548" '
        f'stroke="{s["grid"]}" stroke-width="1.5"/>')
    add(f'<circle cx="70" cy="561" r="5.2" fill="{s["accent"]}"/>')
    add(f'<text x="82" y="566" fill="{s["sub"]}" font-family="{mono}" '
        f'font-size="14">reported field (locator.field)</text>')
    legend_two = 82 + tw("reported field (locator.field)", 14) + 26
    add(f'<circle cx="{legend_two + 6:.1f}" cy="561" r="4.8" fill="none" '
        f'stroke="{s["accent"]}" stroke-width="1.6"/>')
    add(f'<text x="{legend_two + 18:.1f}" y="566" fill="{s["sub"]}" '
        f'font-family="{mono}" font-size="14">compared field</text>')
    legend_three = legend_two + 18 + tw("compared field", 14) + 26
    add(f'<text x="{legend_three:.1f}" y="566" fill="{s["faint"]}" '
        f'font-family="{mono}" font-size="14">blank = the rule never reads it</text>')

    left_out = "hit → issues[] { ruleId, severity, locator(row, field), found, expected, fix }"
    right_out = "cannot run → skipped[] { rule, reason }"
    check(left_out, 14, 700, "outcome line")
    add(f'<text x="{LABEL_X}" y="587" fill="{s["sub"]}" font-family="{mono}" '
        f'font-size="14">{escape(left_out)}</text>')
    add(f'<text x="{CARD[2] - 24}" y="587" text-anchor="end" fill="{s["warn"]}" '
        f'font-family="{mono}" font-size="14">{escape(right_out)}</text>')

    # --- footer ------------------------------------------------------------
    add(f'<text x="44" y="630" fill="{s["faint"]}" font-family="{mono}" '
        f'font-size="14">Apache-2.0 · read-only · no network · no writes</text>')
    footer_right = "rules/demurrage-ledger.yaml · v2026.1 · severity warn ×7"
    check(footer_right, 14, 640, "footer right")
    add(f'<text x="1056" y="630" text-anchor="end" fill="{s["sub"]}" '
        f'font-family="{mono}" font-size="14">{escape(footer_right)}</text>')
    add("</svg>")
    svg = "\n".join(parts) + "\n"
    ET.fromstring(svg.encode("utf-8"))
    return svg


# --------------------------------------------------------------------------- #


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    written: list[str] = []
    for skin_name in ("light", "dark"):
        for lang in ("zh", "en"):
            written.append(hero(lang, skin_name))
        name = f"dsh-demurrage-ledger-flow-v5-{skin_name}.svg"
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as handle:
            handle.write(svg_flow(skin_name))
        written.append(name)
    for name in written:
        print(f"wrote docs/assets/{name}")


if __name__ == "__main__":
    main()
