#!/usr/bin/env python3
"""Render the 19 November 2026 world-news front page as a 1024x1024 PNG.

Template "The Daily News" (approved layout): tracked top bar, big serif
masthead, section nav + 3px red rule, red date bar, hero story #1 with a
flat three-flag illustration + right rail #2-4, feature strip #5-8 with
pictograms, dotted-number world map, 24-item list in 3 columns, DATE CHECK
strip, footer legend. 34 stories claimed, 32 shown (template precedent).

Font-fix v3.1: Noto family only, letter tracking on caps, fixed sizes
(never shrink per item), word-boundary truncation with an ellipsis,
vertically centred text, uniform pill width, >=12px text-to-pill gap,
region tags <=8 letters (MIDEAST), footer legend squares drawn as
rectangles (Noto has no U+25A0 glyph).

Run: python3 render.py  ->  writes entry.png next to this file.
Deterministic: no network, no randomness, no clock. Pillow is a local
build-time tool only; the submitted entrypoint (main.py) is stdlib-only
and just copies the PNG this script draws.
"""

import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MARGIN = 24
LEFT = MARGIN
RIGHT = W - MARGIN
CW = RIGHT - LEFT  # 976

# ---- palette ------------------------------------------------------------
PAPER = (247, 242, 231)
INK = (26, 26, 26)
GRAY = (110, 105, 92)
RULE = (216, 208, 188)
BEIGE = (233, 225, 203)
BEIGE_DARK = (222, 212, 186)
RED = (160, 30, 40)
RED_DARK = (140, 22, 32)
GOLD = (201, 162, 39)
GOLD_DARK = (140, 122, 31)
SEA = (199, 217, 228)
SEA_GRID = (178, 200, 214)
LAND = (163, 177, 138)
WHITE = (255, 255, 255)
BLACK = (26, 26, 26)
DATECHECK_BG = (240, 226, 184)

REGION = {
    "ASIA": (46, 122, 184),
    "EUROPE": (43, 76, 155),
    "MIDEAST": (168, 91, 35),
    "AMERICAS": (108, 79, 160),
    "CLIMATE": (31, 138, 122),
    "ECONOMY": (140, 122, 31),
    "AFRICA": (138, 90, 40),
    "OCEANIA": (15, 107, 140),
    "TECH": (91, 45, 142),
    "ASIA-PAC": (58, 125, 68),
}

# ---- stories (all happened / first reported Thu 19 Nov 2026) -----------
TOP = [
    {
        "n": 1, "tag": "ASIA", "art": "flags",
        "head": "TRUMP, XI, PUTIN ISSUE PEACE DECLARATION",
        "sub": "First three-way summit in Shenzhen; Ukraine not mentioned",
    },
    {
        "n": 2, "tag": "ASIA",
        "head": "ICJ: MYANMAR COMMITTED GENOCIDE",
        "sub": "First ruling of its kind in Rohingya case",
    },
    {
        "n": 3, "tag": "CLIMATE",
        "head": "CYCLONE AKVAN NEARS INDIA COAST",
        "sub": "72,000 evacuated; landfall due Friday",
    },
    {
        "n": 4, "tag": "EUROPE",
        "head": "KERCH BRIDGE HIT FOR THIRD TIME",
        "sub": "Rail traffic halted after strike",
    },
    {
        "n": 5, "tag": "ECONOMY", "art": "bars",
        "head": "ANTHROPIC'S RECORD $81.3BN IPO",
        "sub": "Shares at $83 in biggest debut ever",
    },
    {
        "n": 6, "tag": "EUROPE", "art": "dkgl",
        "head": "DENMARK OKS GREENLAND-US DEAL",
        "sub": "Unanimous vote opens Arctic bases",
    },
    {
        "n": 7, "tag": "ASIA", "art": "flame",
        "head": "BANGLADESH UNREST TURNS DEADLY",
        "sub": "4 killed; Yunus home torched",
    },
    {
        "n": 8, "tag": "AFRICA", "art": "boat",
        "head": "MIGRANT BOAT SINKS OFF SENEGAL",
        "sub": "Dozens missing; ~100 aboard",
    },
]

# 24 list items: (headline, subhead, tag, status)  C=confirmed, D=developing
LIST24 = [
    ("Trump delays Iran call", "Weighs strike as Israel presses", "MIDEAST", "D"),
    ("Russian strikes kill 5", "Power cut across five regions", "EUROPE", "C"),
    ("IAEA: N. Korea expands", "Grossi warns IAEA board", "ASIA", "C"),
    ("COP31 enters final lap", "Fossil-fuel wording unresolved", "CLIMATE", "C"),
    ("Gas Husky tanker sinks", "LPG ship hit by projectiles", "EUROPE", "C"),
    ("Venezuela ties resume", "Hegseth visits Caracas", "AMERICAS", "C"),
    ("Arizona probes OpenAI", "AG cites 'rogue AI' in banks", "TECH", "C"),
    ("Fiji declares drought", "El Nino drains island water", "OCEANIA", "C"),
    ("US jets hit Qeshm", "Tehran hits back in Gulf", "MIDEAST", "C"),
    ("Odesa strike kills 4", "13 injured as talks go on", "EUROPE", "C"),
    ("Takaichi, Putin talk", "Japan PM holds call with Kremlin", "ASIA-PAC", "C"),
    ("Vanuatu: reform COP31", "Pacific states want adaptation", "OCEANIA", "C"),
    ("Van Gogh sells $190.4M", "Record price despite Nazi-era row", "EUROPE", "C"),
    ("Haiti plot pastor guilty", "Convicted on all 8 counts", "AMERICAS", "C"),
    ("Bitcoin under $63,000", "ETFs see $157.8M in outflows", "ECONOMY", "C"),
    ("Seoul court clears ex-PM", "Martial-law conviction overturned", "ASIA-PAC", "C"),
    ("Hormuz tankers mined", "Fires reported; oil at risk", "MIDEAST", "D"),
    ("Kursk, Tatarstan hit", "11 hurt; oil tanks burn", "EUROPE", "C"),
    ("Lee urges North talks", "Seoul seeks dialogue", "ASIA-PAC", "C"),
    ("NZ pay equity ruling", "Landmark win for workers", "OCEANIA", "C"),
    ("Harry: would serve again", "Duke speaks on military service", "EUROPE", "C"),
    ("Salvador troops to Haiti", "Security mission grows in Haiti", "AMERICAS", "C"),
    ("Houthis hit Riyadh", "PIF tower damaged in attack", "MIDEAST", "C"),
    ("IDF ends Gaza ground op", "Tanks pushed past Yellow Line", "MIDEAST", "C"),
]

# Map pins: (lon, lat) for stories 1-8.
PINS = [
    (114.1, 22.5),   # 1 Shenzhen
    (4.3, 52.1),     # 2 Den Haag
    (80.5, 16.5),    # 3 Andhra coast
    (36.5, 45.3),    # 4 Kerch
    (-120.5, 38.0),  # 5 San Francisco area
    (12.6, 55.7),    # 6 Copenhagen
    (90.4, 23.8),    # 7 Dhaka
    (-16.0, 15.0),   # 8 Senegal coast
]

# Coarse continent outlines in (lon, lat), equirectangular.
LAND_POLYS = [
    # North America
    [(-168, 66), (-140, 70), (-125, 71), (-110, 68), (-95, 69), (-85, 66),
     (-80, 73), (-70, 62), (-65, 60), (-55, 52), (-60, 47), (-70, 44),
     (-75, 35), (-80, 32), (-81, 26), (-84, 30), (-90, 21), (-97, 26),
     (-105, 20), (-110, 23), (-115, 29), (-125, 40), (-125, 49),
     (-135, 60), (-155, 58), (-165, 60)],
    # Greenland
    [(-55, 60), (-45, 60), (-40, 64), (-30, 68), (-22, 70), (-25, 76),
     (-40, 80), (-58, 76), (-60, 70)],
    # South America
    [(-80, 10), (-75, 10), (-70, 12), (-62, 10), (-55, 6), (-52, 4),
     (-50, 0), (-45, -3), (-38, -5), (-35, -9), (-40, -15), (-40, -22),
     (-48, -28), (-55, -35), (-62, -41), (-65, -45), (-68, -50),
     (-70, -54), (-73, -50), (-73, -40), (-72, -30), (-70, -20),
     (-75, -15), (-80, -8), (-81, -4), (-80, 2)],
    # Africa
    [(-17, 15), (-10, 6), (-5, 5), (0, 6), (6, 4), (9, 4), (12, -2),
     (13, -8), (12, -17), (15, -27), (18, -32), (20, -35), (28, -33),
     (32, -28), (35, -22), (40, -15), (42, -10), (46, -2), (51, 2),
     (51, 11), (44, 11), (40, 15), (38, 20), (35, 28), (30, 31), (20, 32),
     (10, 33), (0, 36), (-6, 35), (-10, 31), (-15, 27), (-17, 20)],
    # Europe
    [(-10, 36), (-9, 43), (-2, 48), (-5, 50), (0, 51), (3, 53), (8, 55),
     (8, 57), (10, 59), (5, 60), (5, 62), (12, 64), (18, 69), (25, 71),
     (30, 70), (32, 68), (35, 66), (40, 64), (42, 60), (40, 58), (35, 55),
     (30, 55), (28, 58), (24, 60), (21, 55), (20, 54), (18, 56), (15, 55),
     (12, 54), (8, 57), (5, 53), (3, 51), (-2, 50), (-5, 48), (-2, 44),
     (-2, 43), (-9, 43), (-10, 38)],
    # Asia (mainland, simplified)
    [(30, 36), (35, 36), (36, 33), (40, 31), (43, 29), (48, 29), (50, 26),
     (55, 25), (58, 23), (60, 25), (62, 25), (66, 25), (70, 20), (72, 20),
     (75, 15), (77, 8), (80, 10), (80, 15), (85, 19), (88, 22), (91, 22),
     (93, 18), (95, 16), (98, 10), (100, 8), (103, 2), (104, 1), (100, 5),
     (98, 10), (95, 15), (92, 16), (90, 20), (88, 22), (85, 19), (80, 13),
     (77, 8), (75, 10), (73, 16), (70, 20), (66, 25), (62, 25), (58, 26),
     (55, 28), (52, 29), (50, 30), (48, 30), (44, 29), (40, 31), (38, 36),
     (35, 36), (32, 36), (30, 36)],
    # Asia north-east (Siberia to Kamchatka)
    [(32, 68), (40, 68), (50, 69), (60, 69), (70, 72), (80, 73), (90, 75),
     (100, 76), (110, 74), (120, 73), (130, 71), (140, 72), (150, 70),
     (158, 65), (162, 60), (158, 56), (150, 59), (142, 55), (140, 50),
     (138, 45), (135, 43), (132, 43), (130, 42), (127, 40), (122, 38),
     (118, 39), (115, 35), (110, 30), (105, 25), (100, 20), (95, 16),
     (92, 16), (90, 20), (88, 22), (85, 19), (80, 13), (77, 8), (75, 10),
     (73, 16), (70, 20), (66, 25), (62, 25), (58, 26), (55, 28), (52, 29),
     (50, 30), (48, 30), (44, 29), (40, 31), (38, 36), (35, 36), (32, 36),
     (30, 36), (30, 45), (28, 50), (30, 55), (28, 60), (30, 65)],
    # Australia
    [(113, -22), (114, -30), (115, -35), (120, -34), (124, -33), (129, -32),
     (132, -32), (135, -35), (138, -35), (140, -38), (145, -38), (150, -37),
     (153, -32), (153, -27), (150, -22), (146, -19), (142, -15), (142, -11),
     (137, -12), (135, -15), (132, -12), (130, -13), (126, -14),
     (122, -17), (118, -20)],
    # UK
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (1, 51),
     (-3, 50)],
    # Japan
    [(130, 31), (132, 33), (135, 34), (137, 35), (139, 37), (141, 39),
     (141, 41), (142, 44), (144, 44), (141, 42), (139, 38), (136, 35),
     (133, 34), (131, 32)],
    # Indonesia (coarse blobs)
    [(95, 5), (98, 3), (100, -2), (104, -5), (110, -7), (115, -8),
     (120, -9), (125, -9), (130, -4), (132, -1), (128, 1), (122, 0),
     (115, 0), (108, -3), (103, -1), (98, 2)],
    # New Zealand
    [(167, -45), (170, -42), (173, -40), (175, -38), (177, -38),
     (174, -41), (172, -43), (168, -46)],
    # Madagascar
    [(44, -16), (47, -15), (50, -16), (49, -20), (46, -24), (44, -25),
     (43, -21)],
]

FONT_DIR = "/usr/share/fonts/truetype/noto"


def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


F_SERIF = lambda s: font("NotoSerif-Bold.ttf", s)
F_BOLD = lambda s: font("NotoSans-Bold.ttf", s)
F_SEMI = lambda s: font("NotoSans-SemiBold.ttf", s)
F_REG = lambda s: font("NotoSans-Regular.ttf", s)


# ---- text helpers --------------------------------------------------------
def text_w(d, s, f, tracking=0.0):
    """Width of s in font f with extra tracking px between glyphs."""
    if not s:
        return 0.0
    w = 0.0
    for ch in s:
        w += d.textlength(ch, font=f) + tracking
    return w - tracking


def draw_tracked(d, x, y_center, s, f, fill, tracking=0.0, anchor_left=True):
    """Draw s char by char, vertically centred on y_center. Returns width."""
    cx = x
    for ch in s:
        d.text((cx, y_center), ch, font=f, fill=fill, anchor="lm")
        cx += d.textlength(ch, font=f) + tracking
    return cx - x - (tracking if s else 0)


def draw_tracked_center(d, cx, y_center, s, f, fill, tracking=0.0):
    w = text_w(d, s, f, tracking)
    draw_tracked(d, cx - w / 2.0, y_center, s, f, fill, tracking)
    return w


def fit_line(d, s, f, max_w, tracking=0.0):
    """Truncate s at a word boundary + ellipsis so it fits max_w."""
    if text_w(d, s, f, tracking) <= max_w:
        return s
    words = s.split(" ")
    out = ""
    for word in words:
        cand = (out + " " + word).strip()
        if text_w(d, cand + "…", f, tracking) <= max_w:
            out = cand
        else:
            break
    if not out:
        out = words[0]
        while out and text_w(d, out + "…", f, tracking) > max_w:
            out = out[:-1]
    return out + "…"


def wrap_lines(d, s, f, max_w, max_lines, tracking=0.0):
    """Greedy word wrap to at most max_lines; last line truncated at a
    word boundary + ellipsis when it still overflows."""
    words = s.split(" ")
    lines = []
    cur = ""
    for word in words:
        cand = (cur + " " + word).strip()
        if text_w(d, cand, f, tracking) <= max_w:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = word
            if len(lines) == max_lines:
                break
    if len(lines) < max_lines and cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    if lines and text_w(d, lines[-1], f, tracking) > max_w:
        lines[-1] = fit_line(d, lines[-1], f, max_w, tracking)
    return lines


def draw_lines(d, x, y_top, lines, f, fill, line_h, tracking=0.0):
    for i, line in enumerate(lines):
        d.text((x, y_top + i * line_h), line, font=f, fill=fill, anchor="la")


# ---- small drawing helpers ----------------------------------------------
def star(d, cx, cy, r, fill):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, fill=fill)


def flag_us(d, x, y, w, h):
    stripe = h / 13.0
    for i in range(13):
        c = (178, 34, 52) if i % 2 == 0 else WHITE
        d.rectangle([x, y + i * stripe, x + w, y + (i + 1) * stripe], fill=c)
    cw, ch = w * 0.4, stripe * 7
    d.rectangle([x, y, x + cw, y + ch], fill=(60, 59, 110))
    for r in range(5):
        for c in range(6):
            sx = x + cw * (c + 0.5) / 6
            sy = y + ch * (r + 0.5) / 5
            d.ellipse([sx - 1.4, sy - 1.4, sx + 1.4, sy + 1.4], fill=WHITE)


def flag_cn(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(222, 41, 16))
    star(d, x + w * 0.22, y + h * 0.28, h * 0.22, (255, 222, 0))
    for sx, sy in [(0.48, 0.14), (0.60, 0.24), (0.60, 0.42), (0.48, 0.52)]:
        star(d, x + w * sx, y + h * sy, h * 0.08, (255, 222, 0))


def flag_ru(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h / 3], fill=WHITE)
    d.rectangle([x, y + h / 3, x + w, y + 2 * h / 3], fill=(0, 57, 166))
    d.rectangle([x, y + 2 * h / 3, x + w, y + h], fill=(213, 0, 50))


def flag_dk(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(200, 16, 46))
    d.rectangle([x + w * 0.30, y, x + w * 0.42, y + h], fill=WHITE)
    d.rectangle([x, y + h * 0.40, x + w, y + h * 0.60], fill=WHITE)


def flag_gl(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h / 2], fill=WHITE)
    d.rectangle([x, y + h / 2, x + w, y + h], fill=(213, 0, 50))
    d.ellipse([x + w * 0.32, y + h * 0.22, x + w * 0.68, y + h * 0.78],
              fill=(213, 0, 50))
    d.rectangle([x + w * 0.32, y + h * 0.50, x + w * 0.68, y + h * 0.78],
                fill=WHITE)
    d.ellipse([x + w * 0.32, y + h * 0.22, x + w * 0.68, y + h * 0.78],
              outline=(213, 0, 50))


def pic_bars(d, cx, cy, s):
    # Rising bar chart, teal/blue.
    cols = [(46, 122, 184), (31, 138, 122), (43, 76, 155), (201, 162, 39)]
    bw = s * 0.16
    gap = s * 0.07
    total = 4 * bw + 3 * gap
    x0 = cx - total / 2
    heights = [0.35, 0.55, 0.72, 0.95]
    for i, hh in enumerate(heights):
        bx = x0 + i * (bw + gap)
        by = cy + s * 0.42 - s * 0.85 * hh
        d.rectangle([bx, by, bx + bw, cy + s * 0.42], fill=cols[i])
    d.rectangle([x0 - 3, cy + s * 0.42, x0 + total + 3, cy + s * 0.48],
                fill=INK)


def pic_flame(d, cx, cy, s):
    outer = [(cx - s * 0.34, cy + s * 0.42), (cx - s * 0.30, cy - s * 0.05),
             (cx - s * 0.12, cy - s * 0.30), (cx, cy - s * 0.48),
             (cx + s * 0.10, cy - s * 0.22), (cx + s * 0.32, cy - s * 0.02),
             (cx + s * 0.30, cy + s * 0.42)]
    d.polygon(outer, fill=(214, 90, 20))
    inner = [(cx - s * 0.16, cy + s * 0.42), (cx - s * 0.14, cy + s * 0.10),
             (cx, cy - s * 0.12), (cx + s * 0.14, cy + s * 0.10),
             (cx + s * 0.16, cy + s * 0.42)]
    d.polygon(inner, fill=(255, 200, 40))


def pic_boat(d, cx, cy, s):
    # Hull + sail + waves.
    d.polygon([(cx - s * 0.42, cy + s * 0.10), (cx + s * 0.42, cy + s * 0.10),
               (cx + s * 0.28, cy + s * 0.38), (cx - s * 0.28, cy + s * 0.38)],
              fill=(43, 76, 155))
    d.polygon([(cx, cy - s * 0.42), (cx, cy + s * 0.08),
               (cx + s * 0.34, cy + s * 0.08)], fill=WHITE,
              outline=(120, 120, 120))
    d.line([cx, cy - s * 0.42, cx, cy + s * 0.10], fill=INK, width=2)
    for wy in (0.46,):
        d.arc([cx - s * 0.5, cy + s * wy - 4, cx - s * 0.1, cy + s * wy + 4],
              0, 180, fill=(46, 122, 184), width=2)
        d.arc([cx - s * 0.05, cy + s * wy - 4, cx + s * 0.35, cy + s * wy + 4],
              0, 180, fill=(46, 122, 184), width=2)


def draw_pill(d, x, y, w, h, text, color, f):
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=color)
    # anchor="mm" centres the text ON the given point: use the pill centre.
    d.text((x + w / 2, y + h / 2), text, font=f, fill=WHITE, anchor="mm")


def num_badge(d, cx, cy, r, n, fill=RED):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)
    f = F_BOLD(15 if r >= 14 else 13)
    d.text((cx, cy), str(n), font=f, fill=WHITE, anchor="mm")


# ---- map -----------------------------------------------------------------
def project(x0, y0, w, h, lon, lat):
    # equirectangular, lon -180..180, lat 75..-60
    px = x0 + (lon + 180.0) / 360.0 * w
    py = y0 + (75.0 - lat) / 135.0 * h
    return px, py


def draw_map(d, x0, y0, w, h):
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=SEA)
    for lon in range(-150, 181, 30):
        px, _ = project(x0, y0, w, h, lon, 0)
        d.line([px, y0, px, y0 + h], fill=SEA_GRID, width=1)
    for lat in (-60, -30, 0, 30, 60):
        _, py = project(x0, y0, w, h, 0, lat)
        d.line([x0, py, x0 + w, py], fill=SEA_GRID, width=1)
    for poly in LAND_POLYS:
        pts = [project(x0, y0, w, h, lon, lat) for lon, lat in poly]
        d.polygon(pts, fill=LAND)
    f_pin = F_BOLD(11)
    for i, (lon, lat) in enumerate(PINS, start=1):
        px, py = project(x0, y0, w, h, lon, lat)
        d.ellipse([px - 11, py - 11, px + 11, py + 11], fill=RED,
                  outline=WHITE, width=1)
        d.text((px, py), str(i), font=f_pin, fill=WHITE, anchor="mm")


# ---- build ---------------------------------------------------------------
def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # Pill width: uniform, from the longest tag used this edition + padding.
    f_pill = F_BOLD(11)
    tags = sorted({s["tag"] for s in TOP} | {t for _, _, t, _ in LIST24})
    pill_w = max(d.textlength(t, font=f_pill) for t in tags) + 18
    pill_w = int(math.ceil(pill_w))
    pill_h = 18

    # -- top bar -----------------------------------------------------------
    d.line([LEFT, 8, RIGHT, 8], fill=INK, width=1)
    f_top = F_BOLD(13)
    draw_tracked(d, LEFT, 24, "ONE DAY, ONE IMAGE", f_top, INK, 1.5)
    r_txt = "34 SOURCED STORIES • SIX CONTINENTS"
    draw_tracked(d, RIGHT - text_w(d, r_txt, f_top, 1.5), 24, r_txt,
                 f_top, INK, 1.5)
    d.line([LEFT, 36, RIGHT, 36], fill=INK, width=1)

    # -- masthead ----------------------------------------------------------
    mast = "THE WORLD IN ONE PAGE"
    size = 76
    while size > 40:
        f_m = F_SERIF(size)
        if d.textlength(mast, font=f_m) <= CW:
            break
        size -= 1
    d.text((W / 2, 76), mast, font=f_m, fill=INK, anchor="mm")

    # -- nav bar + red rule -------------------------------------------------
    d.rectangle([LEFT, 116, RIGHT, 140], fill=BEIGE)
    nav = "MIDDLE EAST  |  ASIA  |  AMERICAS  |  EUROPE  |  CLIMATE  |  ECONOMY"
    draw_tracked_center(d, W / 2, 128, nav, F_BOLD(15), INK, 0.8)
    d.rectangle([LEFT, 142, RIGHT, 145], fill=RED)

    # -- date bar -----------------------------------------------------------
    d.rectangle([LEFT, 148, RIGHT, 190], fill=RED)
    draw_tracked_center(d, W / 2, 169, "THURSDAY • 19 NOVEMBER 2026",
                        F_BOLD(30), WHITE, 2.0)

    # -- hero + right rail --------------------------------------------------
    hero = TOP[0]
    # image band with three flags
    d.rectangle([LEFT, 196, 620, 280], fill=BEIGE)
    fw, fh = 178, 62
    fx = LEFT + (596 - (3 * fw + 2 * 12)) / 2
    fy = 196 + (84 - fh) / 2
    flag_us(d, fx, fy, fw, fh)
    flag_cn(d, fx + fw + 12, fy, fw, fh)
    flag_ru(d, fx + 2 * (fw + 12), fy, fw, fh)
    num_badge(d, 40, 212, 15, 1)
    # headline (30, max 2 lines) + subhead + pill
    f_hero = F_BOLD(30)
    h_lines = wrap_lines(d, hero["head"], f_hero, 596, 2)
    draw_lines(d, LEFT, 286, h_lines, f_hero, INK, 31)
    d.text((LEFT, 352), fit_line(d, hero["sub"], F_REG(14), 596),
           font=F_REG(14), fill=GRAY, anchor="la")
    draw_pill(d, LEFT, 368, pill_w, 20, hero["tag"], REGION[hero["tag"]],
              f_pill)

    # right rail #2-4
    rail_x = 636
    rail_w = RIGHT - rail_x
    for i, story in enumerate(TOP[1:4]):
        top = 196 + i * 63
        if i:
            d.line([rail_x, top - 1, RIGHT, top - 1], fill=RULE, width=1)
        box = 54
        d.rectangle([rail_x, top + 4, rail_x + box, top + 4 + box],
                    fill=REGION[story["tag"]])
        d.text((rail_x + box / 2, top + 4 + box / 2), str(story["n"]),
               font=F_BOLD(24), fill=WHITE, anchor="mm")
        tx = rail_x + box + 10
        tw = RIGHT - tx
        f_rh = F_BOLD(17)
        r_lines = wrap_lines(d, story["head"], f_rh, tw, 2)
        block_h = len(r_lines) * 20 + 4 + 15
        y0 = top + (63 - block_h) / 2
        draw_lines(d, tx, y0, r_lines, f_rh, INK, 20)
        d.text((tx, y0 + len(r_lines) * 20 + 4),
               fit_line(d, story["sub"], F_REG(12), tw),
               font=F_REG(12), fill=GRAY, anchor="la")

    # -- feature strip #5-8 ---------------------------------------------------
    card_w = 238
    for i, story in enumerate(TOP[4:8]):
        cx0 = LEFT + i * (card_w + 8)
        # pictogram band
        d.rectangle([cx0, 392, cx0 + card_w, 448], fill=BEIGE)
        pcx, pcy = cx0 + card_w / 2, 420
        if story["art"] == "bars":
            pic_bars(d, pcx, pcy, 46)
        elif story["art"] == "dkgl":
            flag_dk(d, pcx - 62, pcy - 16, 56, 32)
            flag_gl(d, pcx + 6, pcy - 16, 56, 32)
        elif story["art"] == "flame":
            pic_flame(d, pcx, pcy, 46)
        elif story["art"] == "boat":
            pic_boat(d, pcx, pcy, 46)
        num_badge(d, cx0 + 14, 406, 13, story["n"])
        # headline (19, max 2 lines) + subhead + pill
        f_fh = F_BOLD(19)
        f_lines = wrap_lines(d, story["head"], f_fh, card_w, 2)
        draw_lines(d, cx0, 452, f_lines, f_fh, INK, 21)
        d.text((cx0, 494), fit_line(d, story["sub"], F_REG(13), card_w),
               font=F_REG(13), fill=GRAY, anchor="la")
        draw_pill(d, cx0, 510, pill_w, pill_h, story["tag"],
                  REGION[story["tag"]], f_pill)

    # -- map ------------------------------------------------------------------
    d.text((LEFT, 536), "WHERE IT HAPPENED", font=F_BOLD(16), fill=INK,
           anchor="la")
    m_txt = "NUMBERS MATCH THE 8 TOP STORIES"
    d.text((RIGHT - d.textlength(m_txt, font=F_BOLD(13)), 538), m_txt,
           font=F_BOLD(13), fill=GRAY, anchor="la")
    draw_map(d, LEFT, 558, CW, 102)

    # -- list: 24 more stories ----------------------------------------------
    d.text((LEFT, 666), "THE REST OF THE DAY", font=F_BOLD(16), fill=INK,
           anchor="la")
    r24 = "24 MORE STORIES"
    d.text((RIGHT - d.textlength(r24, font=F_BOLD(16)), 666), r24,
           font=F_BOLD(16), fill=GOLD_DARK, anchor="la")
    d.line([LEFT, 692, RIGHT, 692], fill=INK, width=1)
    col_w = 318
    col_x = [LEFT, LEFT + col_w + 11, LEFT + 2 * (col_w + 11)]
    f_lh = F_SEMI(17)
    f_ls = F_REG(13)
    for idx, (head, sub, tag, status) in enumerate(LIST24):
        col = idx // 8
        row = idx % 8
        x0 = col_x[col]
        top = 696 + row * 34.5
        sq = GOLD if status == "C" else BLACK
        d.rectangle([x0, top + 7, x0 + 10, top + 17], fill=sq)
        tx = x0 + 16
        max_tw = col_w - 16 - pill_w - 12
        d.text((tx, top + 1), fit_line(d, head, f_lh, max_tw),
               font=f_lh, fill=INK, anchor="la")
        d.text((tx, top + 19), fit_line(d, sub, f_ls, max_tw),
               font=f_ls, fill=GRAY, anchor="la")
        draw_pill(d, x0 + col_w - pill_w, top + 8, pill_w, pill_h, tag,
                  REGION[tag], f_pill)

    # -- DATE CHECK strip ------------------------------------------------------
    d.rectangle([LEFT, 974, RIGHT, 998], fill=DATECHECK_BG,
                outline=BEIGE_DARK, width=1)
    dc_label = "DATE CHECK"
    lx = LEFT + 10
    draw_tracked(d, lx, 986, dc_label, F_BOLD(12), RED, 0.6)
    dc_text = ("34 stories, all 19 Nov 2026. Cut as 18 Nov: Musk remarks, "
               "Jeffries vote, Brand video.")
    tx = lx + text_w(d, dc_label, F_BOLD(12), 0.6) + 10
    d.text((tx, 986), dc_text, font=F_REG(12), fill=INK, anchor="lm")
    src = "SOURCES: REUTERS, AP, NYT, BBC, IMD"
    d.text((RIGHT - 10 - d.textlength(src, font=F_BOLD(11)), 986), src,
           font=F_BOLD(11), fill=GRAY, anchor="lm")

    # -- footer -----------------------------------------------------------------
    fy = 1011
    f_ft = F_BOLD(11)
    x = LEFT
    d.rectangle([x, fy - 5, x + 10, fy + 5], fill=GOLD)
    x += 14
    x += draw_tracked(d, x, fy, "CONFIRMED", f_ft, INK, 0.5)
    x += 14
    d.rectangle([x, fy - 5, x + 10, fy + 5], fill=BLACK)
    x += 14
    x += draw_tracked(d, x, fy, "DEVELOPING", f_ft, INK, 0.5)
    x += 16
    foot = ("All 34 stories happened, or were first reported, on Thursday "
            "19 November 2026; claims are attributed.")
    d.text((x, fy), foot, font=F_REG(11), fill=INK, anchor="lm")

    return img


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "entry.png")
    build().save(out, format="PNG")
    print("wrote", out)


if __name__ == "__main__":
    main()
