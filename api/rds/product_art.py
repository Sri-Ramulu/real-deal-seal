"""Product illustrations, drawn from a product's name and tags.

Flat 2D drawings in the site's style (same 320x190 frame and ground shadow as the home page tiles), tinted with the
product's own color. Every shop's products get the same treatment, so a picture never makes one shop look better
than another. Served as SVG by /api/products/{sku}/image.svg.
"""
from __future__ import annotations

import re
from html import escape

INK, PAPER, GREY, RED = "#0a0a0a", "#ffffff", "#d9d9d9", "#d9201f"

COLORS = [  # most specific first
    ("purple dusk", "#8a6aa8"), ("royal purple", "#5b2d91"), ("indigo tide", "#2f4a7a"), ("brick red", "#a63a2a"),
    ("lavender", "#b8a2d6"), ("indigo", "#33407a"), ("navy", "#24305c"), ("plum", "#6b2a5a"), ("mulberry", "#7a2348"),
    ("heather", "#9b8aaa"), ("purple", "#6e3fa0"), ("harvest", "#c8752a"), ("orange", "#c8752a"), ("sage", "#8fa58a"),
    ("sand", "#d8c39a"), ("canvas", "#d6c8ab"), ("natural", "#d6c8ab"), ("linen", "#ddd2bd"), ("waterproof", "#3f6f8f"),
    ("blue", "#33407a"), ("terracotta", "#c46a43"), ("walnut", "#6b4a2e"), ("acacia", "#a0703f"), ("copper", "#b87333"),
    ("cream", "#efe6d2"), ("ivory", "#f1ead8"), ("charcoal", "#3d3d3d"), ("lilac", "#c3a6d6"), ("rose", "#d48a9a"),
    ("olive", "#6f7a3a"), ("mustard", "#d4a62a"), ("teal", "#2f7a7a"), ("white", "#f4f1ea"), ("gray", "#9a9a9a"),
    ("grey", "#9a9a9a"), ("green", "#4d7a4a"),
]
PATTERNS = ("checked", "gingham", "stripe", "scallop")

TYPES = [  # (type, words that identify it), most specific first
    ("kettle", ("kettle",)), ("mug", ("mug",)), ("planter", ("planter", "plant pot")), ("candle", ("candle",)),
    ("board", ("cutting board", "serving board")), ("rug", ("rug",)), ("vase", ("vase",)), ("bathtowel", ("bath towel", "hand towel")),
    ("sheets", ("sheet set", "duvet", "pillowcase", "quilt")),
    ("picnic", ("picnic blanket",)), ("kneeling", ("kneeling pad", "kneeler")), ("shade", ("shade sail", "shade cloth")),
    ("tote", ("tote",)), ("bread", ("bread basket",)), ("basket", ("storage basket",)), ("mitts", ("oven mitt",)), ("towels", ("dish towel", "tea towel")),
    ("apron", ("apron",)), ("placemats", ("placemat",)), ("runner", ("table runner",)), ("tablecloth", ("tablecloth",)),
    ("curtain", ("curtain",)), ("napkins", ("napkin",)), ("cushion", ("cushion", "pillow")), ("throw", ("throw", "blanket")),
]


def _shade(hex_color: str, f: float) -> str:
    """f < 1 darkens, f > 1 lightens toward white."""
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    if f <= 1:
        r, g, b = (round(v * f) for v in (r, g, b))
    else:
        r, g, b = (round(v + (255 - v) * (f - 1)) for v in (r, g, b))
    return "#%02x%02x%02x" % (r, g, b)


def classify(name: str, tags: list[str] | None = None) -> tuple[str, str, str | None]:
    """(type, color, pattern) for a product."""
    text = (name + " " + " ".join(tags or [])).lower()
    kind = next((k for k, words in TYPES if any(w in text for w in words)), "throw")
    pattern = next((p for p in PATTERNS if p in name.lower()), None)
    if pattern == "gingham":
        pattern = "checked"
    color = next((c for word, c in COLORS if word in name.lower()), None) or next((c for word, c in COLORS if word in text), None)
    if not color:
        color = {"apron": "#5c5c5c", "mitts": RED, "towels": PAPER, "bread": "#c9a46b", "tablecloth": PAPER,
                 "kneeling": "#4d6b4a", "tote": "#d6c8ab", "shade": "#d8c39a", "mug": "#efe6d2", "planter": "#c46a43",
                 "candle": "#efe6d2", "board": "#a0703f", "rug": "#9a9a9a", "vase": "#efe6d2", "bathtowel": "#f4f1ea",
                 "sheets": "#f4f1ea", "kettle": "#9a9a9a", "basket": "#c9a46b"}.get(kind, "#8c8c8c")
    if pattern == "checked" and color == PAPER:
        color = RED
    return kind, color, pattern


def _defs(color: str) -> str:
    dark = _shade(color, 0.72)
    return (f'<defs><pattern id="chk" width="16" height="16" patternUnits="userSpaceOnUse"><rect width="16" height="16" fill="{PAPER}"/>'
            f'<rect width="8" height="8" fill="{color}" opacity="0.85"/><rect x="8" y="8" width="8" height="8" fill="{color}" opacity="0.85"/>'
            f'<rect x="8" width="8" height="8" fill="{color}" opacity="0.35"/><rect y="8" width="8" height="8" fill="{color}" opacity="0.35"/></pattern>'
            f'<pattern id="str" width="18" height="18" patternUnits="userSpaceOnUse"><rect width="18" height="18" fill="{_shade(color, 1.55)}"/>'
            f'<rect width="18" height="7" fill="{color}"/><rect y="9" width="18" height="2" fill="{dark}"/></pattern></defs>')


def _fill(color: str, pattern: str | None) -> str:
    return "url(#chk)" if pattern == "checked" else "url(#str)" if pattern == "stripe" else color


def _napkins(c, p):
    d, l = _shade(c, 0.75), _shade(c, 1.25)
    return (f'<rect x="92" y="96" width="140" height="62" rx="5" fill="{d}"/><rect x="100" y="80" width="140" height="62" rx="5" fill="{c}"/>'
            f'<rect x="84" y="62" width="140" height="62" rx="5" fill="{l}"/><path d="M84 67 154 124" stroke="{c}" stroke-width="3" opacity="0.6"/>'
            f'<path d="M224 62v34l-34-34z" fill="{c}"/><circle cx="196" cy="110" r="7" fill="none" stroke="{PAPER}" stroke-width="2" opacity="0.7"/>')


def _runner(c, p):
    d, l = _shade(c, 0.7), _shade(c, 1.3)
    fringe = "".join(f'<path d="M{x} 150v10" stroke="{d}" stroke-width="2.5"/>' for x in range(124, 200, 6))
    fringe += "".join(f'<path d="M{x} 64v-8" stroke="{d}" stroke-width="2"/>' for x in range(140, 182, 5))
    return (f'<path d="M24 150h272l-58-86H82z" fill="{GREY}"/><path d="M24 150h272v8H24z" fill="#bdbdbd"/>'
            f'<path d="M120 150h80l-20-86h-40z" fill="{_fill(c, p)}"/><path d="M134 150l12-86M186 150l-12-86" stroke="{l}" stroke-width="2.5" opacity="0.6"/>{fringe}')


def _tablecloth(c, p, name):
    f, d = _fill(c, p), _shade(c, 0.78) if not p else INK
    if "round" in name.lower():
        top = _shade(c, 1.25) if not p else f
        hem = "".join(f"q10 10 20 0" for _ in range(11))
        return (f'<path d="M150 124v44M120 122l-8 46M200 122l8 46" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>'
                f'<path d="M50 64c0 26 4 46 0 62{hem}c-4-16 0-36 0-62z" fill="{f}"/>'
                f'<ellipse cx="160" cy="64" rx="110" ry="28" fill="{top}"/><ellipse cx="160" cy="64" rx="42" ry="11" fill="{PAPER}" opacity="0.55"/>'
                f'<path d="M92 90v34M160 92v34M228 90v34" stroke="{d}" stroke-width="3" opacity="0.35"/>')
    return (f'<path d="M70 50h180l30 30H40z" fill="{f}"/><path d="M40 80h240v74l-20 8-20-8-20 8-20-8-20 8-20-8-20 8-20-8-20 8-20-8-20 8-20-8z" fill="{f}"/>'
            f'<path d="M40 80h240" stroke="{d}" stroke-width="3" opacity="0.5"/><rect x="40" y="80" width="240" height="82" fill="{INK}" opacity="0.06"/>')


def _curtain(c, p):
    d, l = _shade(c, 0.72), _shade(c, 1.2)
    return (f'<path d="M56 30h208" stroke="{INK}" stroke-width="6" stroke-linecap="round"/><circle cx="56" cy="30" r="7" fill="{INK}"/><circle cx="264" cy="30" r="7" fill="{INK}"/>'
            f'<path d="M84 34h152v124c-10 6-20 6-30 0-10 6-20 6-30 0-10 6-20 6-30 0-10 6-20 6-30 0-10 6-20 6-32 0z" fill="{c}"/>'
            + "".join(f'<path d="M{x} 36v118" stroke="{d if i % 2 else l}" stroke-width="7" opacity="0.55"/>' for i, x in enumerate(range(100, 236, 22)))
            + "".join(f'<circle cx="{x}" cy="34" r="5" fill="none" stroke="{INK}" stroke-width="2.5"/>' for x in range(92, 240, 24)))


def _cushion(c, p, name):
    d, l = _shade(c, 0.72), _shade(c, 1.25)
    if "outdoor" in name.lower() or "seat" in name.lower():
        return (f'<path d="M58 104 128 70h134l-62 34z" fill="{l}"/><path d="M58 104h142v44H58z" fill="{c}"/><path d="M200 104l62-34v44l-62 34z" fill="{d}"/>'
                f'<path d="M58 104h142l62-34" fill="none" stroke="{PAPER}" stroke-width="3" opacity="0.7"/>'
                f'<circle cx="112" cy="88" r="5" fill="{d}"/><circle cx="168" cy="88" r="5" fill="{d}"/><circle cx="196" cy="74" r="4" fill="{d}"/>'
                f'<path d="M58 148h142" stroke="{d}" stroke-width="3" opacity="0.6"/>')
    return (f'<path d="M88 46c24 8 120 8 144 0 10 28 10 88 0 114-24-8-120-8-144 0-10-26-10-86 0-114z" fill="{c}"/>'
            f'<path d="M92 54c26 6 110 6 136 0" stroke="{l}" stroke-width="4" opacity="0.6"/><path d="M96 150c26-6 102-6 128 0" stroke="{d}" stroke-width="4" opacity="0.5"/>'
            f'<circle cx="160" cy="103" r="7" fill="{d}"/><path d="M118 103c14 6 70 6 84 0" stroke="{d}" stroke-width="2" opacity="0.5"/>')


def _throw(c, p):
    d, l = _shade(c, 0.72), _shade(c, 1.22)
    fringe = "".join(f'<path d="M{x} 150v14" stroke="{d}" stroke-width="2.5"/>' for x in range(84, 238, 7))
    return (f'<rect x="80" y="96" width="160" height="54" rx="6" fill="{d}"/><rect x="72" y="72" width="176" height="44" rx="8" fill="{c}"/>'
            f'<rect x="80" y="48" width="160" height="40" rx="8" fill="{l}"/><path d="M90 68h140M90 94h140" stroke="{c}" stroke-width="3" opacity="0.7"/>{fringe}')


def _picnic(c, p):
    f = _fill(c, p or "stripe")
    return (f'<rect x="70" y="58" width="180" height="96" rx="10" fill="{f}"/><rect x="70" y="58" width="180" height="96" rx="10" fill="none" stroke="{_shade(c, 0.65)}" stroke-width="3"/>'
            f'<path d="M126 58c0-30 68-30 68 0" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>'
            f'<rect x="110" y="100" width="100" height="16" fill="{INK}"/><rect x="152" y="98" width="16" height="20" rx="3" fill="{GREY}"/>')


def _placemats(c, p):
    d = _shade(c, 0.75)
    return (f'<rect x="44" y="70" width="150" height="92" rx="8" fill="{d}" transform="rotate(-6 119 116)"/>'
            f'<rect x="120" y="54" width="156" height="96" rx="8" fill="{c}"/>'
            + "".join(f'<path d="M132 {y}h132" stroke="{_shade(c, 1.3)}" stroke-width="2" opacity="0.55"/>' for y in range(66, 146, 9))
            + f'<circle cx="198" cy="102" r="34" fill="{PAPER}"/><circle cx="198" cy="102" r="24" fill="none" stroke="{GREY}" stroke-width="3"/>'
            f'<path d="M150 74v56M256 74v56" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>')


def _apron(c, p, name):
    d = _shade(c, 0.7)
    garden = "garden" in name.lower()
    pocket = (f'<rect x="124" y="118" width="72" height="34" rx="4" fill="{d}"/><path d="M160 118v34" stroke="{c}" stroke-width="3"/>'
              f'<path d="M140 118v-26M146 118l8-30M176 118v-22" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>') if garden else \
             f'<rect x="132" y="116" width="56" height="30" rx="4" fill="{d}"/>'
    return (f'<path d="M134 34c0-30 52-30 52 0" fill="none" stroke="{INK}" stroke-width="5"/>'
            f'<path d="M130 28h60v30c0 8 22 10 34 12v94H96V70c12-2 34-4 34-12z" fill="{_fill(c, p)}"/>'
            f'<path d="M96 76c-20 2-34 8-46 16M224 76c20 2 34 8 46 16" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>{pocket}')


def _mitts(c, p):
    f = _fill(c, p)
    mitt = (f'<path d="M0 0c0-26 14-44 34-44s34 18 34 44v56H0z" fill="{f}"/><path d="M0 8c-16 0-26-10-26-24s12-18 22-12" fill="{f}"/>'
            f'<rect x="-4" y="52" width="76" height="16" rx="4" fill="{_shade(c, 0.7) if not p else INK}"/><path d="M60 -20c10 0 16 8 16 18" fill="none" stroke="{INK}" stroke-width="3"/>')
    return f'<g transform="translate(92 100) rotate(-8)">{mitt}</g><g transform="translate(176 96) rotate(8)">{mitt}</g>'


def _towels(c, p, name):
    edge = ""
    if p == "scallop":
        edge = "".join(f'<circle cx="{x}" cy="158" r="7" fill="{RED}"/>' for x in range(104, 220, 14))
    bands = "" if p == "scallop" else f'<rect x="96" y="128" width="128" height="10" fill="{RED}"/><rect x="96" y="142" width="128" height="4" fill="{RED}"/>'
    towel = PAPER if c == PAPER else c
    return (f'<path d="M60 40h200" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>'
            f'<rect x="84" y="40" width="128" height="104" rx="4" fill="{_shade(towel, 0.88) if towel != PAPER else GREY}"/>'
            f'<rect x="96" y="40" width="128" height="116" rx="4" fill="{towel}" stroke="{GREY}" stroke-width="2"/>{bands}{edge}'
            + "".join(f'<path d="M{x} 50v70" stroke="{GREY}" stroke-width="1.5"/>' for x in range(108, 220, 12)))


def _bread(c, p):
    d = _shade(c, 0.75)
    weave = "".join(f'<path d="M{x} 112c4 14 4 30 0 44" stroke="{d}" stroke-width="3"/>' for x in range(86, 238, 16))
    return (f'<ellipse cx="160" cy="70" rx="58" ry="28" fill="#c98a4b"/><path d="M128 60c8-6 16-6 24 0M160 56c8-6 16-6 24 0" stroke="#8a5428" stroke-width="3" fill="none"/>'
            f'<path d="M84 96l40 24 22-22 30 22 40-24" fill="{PAPER}" stroke="{RED}" stroke-width="3"/>'
            f'<path d="M70 104h180l-16 54H86z" fill="{c}"/>{weave}<path d="M70 104h180" stroke="{d}" stroke-width="6"/>')


def _tote(c, p):
    d = _shade(c, 0.75)
    return (f'<path d="M126 70c0-40 68-40 68 0" fill="none" stroke="{INK}" stroke-width="7"/>'
            f'<path d="M96 70h128l10 92H86z" fill="{c}"/><path d="M96 70h128" stroke="{d}" stroke-width="6"/>'
            f'<rect x="130" y="104" width="60" height="36" rx="3" fill="{d}"/><path d="M146 104v-20M174 104v-14" stroke="#4d6b4a" stroke-width="6" stroke-linecap="round"/>'
            f'<path d="M140 86c4-8 12-10 12-10M170 92c4-8 10-8 10-8" stroke="#4d6b4a" stroke-width="4" fill="none"/>')


def _kneeling(c, p):
    d = _shade(c, 0.7)
    return (f'<path d="M62 122 102 62h156l-40 60z" fill="{_shade(c, 1.2)}"/><path d="M62 122h156v30H62z" fill="{c}"/><path d="M218 122l40-60v30l-40 60z" fill="{d}"/>'
            f'<ellipse cx="190" cy="80" rx="22" ry="8" fill="{d}"/><path d="M80 138h120" stroke="{d}" stroke-width="3" opacity="0.6"/>')


def _shade_sail(c, p):
    d = _shade(c, 0.72)
    return (f'<path d="M60 166V40M262 166V60" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>'
            f'<path d="M72 50 250 70 150 128z" fill="{c}"/><path d="M72 50c60 18 92 26 178 20M150 128c4-24 10-40 30-58" stroke="{d}" stroke-width="3" fill="none" opacity="0.6"/>'
            f'<path d="M60 44 72 50M262 64 250 70M150 128 150 166" stroke="{INK}" stroke-width="2"/>')


def _mug(c, p):
    d = _shade(c, 0.72)
    return (f'<path d="M196 94c32 0 32 46 0 46" fill="none" stroke="{d}" stroke-width="11"/>'
            f'<rect x="112" y="72" width="86" height="88" rx="10" fill="{_fill(c, p)}" stroke="{d}" stroke-width="2"/>'
            f'<ellipse cx="155" cy="73" rx="43" ry="8" fill="{d}"/>'
            f'<path d="M140 58c-7-8 7-14 0-24M168 58c-7-8 7-14 0-24" stroke="#bdbdbd" stroke-width="4" fill="none" stroke-linecap="round"/>')


def _planter(c, p):
    d = _shade(c, 0.72)
    return (f'<path d="M160 100c-4-30-30-46-48-48 6 24 24 42 48 48z" fill="#4d6b4a"/><path d="M160 100c2-36 22-58 46-62-2 28-20 50-46 62z" fill="#6b8f5e"/>'
            f'<path d="M160 102V46" stroke="#3d5a3a" stroke-width="4"/>'
            f'<path d="M116 112h88l-12 54h-64z" fill="{c}"/><rect x="106" y="98" width="108" height="18" rx="4" fill="{d}"/>')


def _candle(c, p):
    d = _shade(c, 0.78)
    return (f'<path d="M160 80V64" stroke="{INK}" stroke-width="3"/><path d="M160 36c11 13 11 24 0 30-11-6-11-17 0-30z" fill="#f2a33a"/>'
            f'<rect x="116" y="80" width="88" height="82" rx="8" fill="{c}" stroke="{d}" stroke-width="2"/><rect x="116" y="80" width="88" height="14" rx="4" fill="{d}"/>'
            f'<rect x="132" y="112" width="56" height="28" rx="3" fill="{PAPER}" opacity="0.85"/>')


def _board(c, p):
    d = _shade(c, 0.75)
    grain = "".join(f'<path d="M90 {y}c40-6 90 6 136 0" stroke="{d}" stroke-width="2" fill="none" opacity="0.6"/>' for y in range(86, 142, 14))
    return (f'<path d="M232 108h40" stroke="{c}" stroke-width="24" stroke-linecap="round"/><circle cx="266" cy="108" r="5" fill="{PAPER}"/>'
            f'<rect x="66" y="66" width="176" height="84" rx="18" fill="{c}"/>{grain}<rect x="66" y="66" width="176" height="84" rx="18" fill="none" stroke="{d}" stroke-width="3"/>')


def _rug(c, p):
    d, l = _shade(c, 0.7), _shade(c, 1.3)
    fringe = "".join(f'<path d="M{x} {y}h-12" stroke="{d}" stroke-width="2.5"/>' for x in (60,) for y in range(58, 156, 8))
    fringe += "".join(f'<path d="M{x} {y}h12" stroke="{d}" stroke-width="2.5"/>' for x in (260,) for y in range(58, 156, 8))
    return (f'{fringe}<rect x="60" y="54" width="200" height="104" rx="3" fill="{_fill(c, p)}"/>'
            f'<rect x="74" y="66" width="172" height="80" fill="none" stroke="{l}" stroke-width="5"/>'
            f'<path d="M160 82l34 24-34 24-34-24z" fill="none" stroke="{d}" stroke-width="4"/>')


def _vase(c, p):
    d = _shade(c, 0.75)
    return (f'<path d="M150 54c-6-20-16-30-28-34M170 54c4-22 16-32 28-34M160 54V22" stroke="#4d6b4a" stroke-width="3" fill="none"/>'
            f'<circle cx="122" cy="20" r="6" fill="#d48a9a"/><circle cx="198" cy="20" r="6" fill="#d4a62a"/><circle cx="160" cy="18" r="6" fill="#b8a2d6"/>'
            f'<path d="M138 54h44v14c0 10 26 26 26 56 0 26-20 38-48 38s-48-12-48-38c0-30 26-46 26-56z" fill="{c}" stroke="{d}" stroke-width="2"/>'
            f'<path d="M136 56h48" stroke="{d}" stroke-width="6" stroke-linecap="round"/>')


def _bathtowel(c, p):
    d, l = _shade(c, 0.86), _shade(c, 0.7)
    return (f'<rect x="80" y="106" width="160" height="50" rx="12" fill="{d}" stroke="{GREY}" stroke-width="2"/>'
            f'<rect x="90" y="60" width="140" height="50" rx="12" fill="{c}" stroke="{GREY}" stroke-width="2"/>'
            f'<rect x="90" y="94" width="140" height="6" fill="{l}" opacity="0.6"/><rect x="80" y="140" width="160" height="6" fill="{l}" opacity="0.6"/>')


def _sheets(c, p):
    d, l = _shade(c, 0.82), _shade(c, 1.15)
    return (f'<rect x="74" y="112" width="172" height="40" rx="6" fill="{d}" stroke="{GREY}" stroke-width="2"/>'
            f'<rect x="68" y="80" width="184" height="40" rx="6" fill="{_fill(c, p)}" stroke="{GREY}" stroke-width="2"/>'
            f'<rect x="80" y="50" width="160" height="38" rx="6" fill="{l}" stroke="{GREY}" stroke-width="2"/>'
            f'<path d="M160 50v102" stroke="{RED}" stroke-width="5" opacity="0.8"/><rect x="146" y="58" width="28" height="14" rx="2" fill="{PAPER}"/>')


def _kettle(c, p):
    d = _shade(c, 0.7)
    return (f'<path d="M128 90c0-34 64-34 64 0" fill="none" stroke="{INK}" stroke-width="7"/>'
            f'<path d="M106 120c-20-6-32-22-40-36" stroke="{c}" stroke-width="12" stroke-linecap="round"/>'
            f'<path d="M102 162c-8-40 2-74 58-74s66 34 58 74z" fill="{c}" stroke="{d}" stroke-width="3"/>'
            f'<ellipse cx="160" cy="90" rx="22" ry="6" fill="{d}"/><circle cx="160" cy="82" r="5" fill="{INK}"/>')


def _basket(c, p):
    d = _shade(c, 0.72)
    weave = "".join(f'<path d="M{x} 86v70" stroke="{d}" stroke-width="3"/>' for x in range(92, 232, 14))
    weave += "".join(f'<path d="M80 {y}h160" stroke="{d}" stroke-width="2" opacity="0.6"/>' for y in range(100, 156, 12))
    return (f'<path d="M80 84h160l-10 76H90z" fill="{c}"/>{weave}<rect x="74" y="78" width="172" height="12" rx="4" fill="{d}"/>'
            f'<path d="M96 84c0-18 20-18 20 0M204 84c0-18 20-18 20 0" fill="none" stroke="{d}" stroke-width="5"/>')


DRAW = {"napkins": _napkins, "runner": _runner, "curtain": _curtain, "throw": _throw, "picnic": _picnic, "placemats": _placemats,
        "mitts": _mitts, "bread": _bread, "tote": _tote, "kneeling": _kneeling, "shade": _shade_sail, "mug": _mug, "planter": _planter,
        "candle": _candle, "board": _board, "rug": _rug, "vase": _vase, "bathtowel": _bathtowel, "sheets": _sheets, "kettle": _kettle,
        "basket": _basket}
DRAW_NAMED = {"tablecloth": _tablecloth, "cushion": _cushion, "apron": _apron, "towels": _towels}


def svg(name: str, tags: list[str] | None = None) -> str:
    kind, color, pattern = classify(name, tags)
    body = DRAW_NAMED[kind](color, pattern, name) if kind in DRAW_NAMED else DRAW[kind](color, pattern)
    title = escape(re.sub(r"\s+", " ", name).strip())
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 190" role="img" aria-label="{title}"><title>{title}</title>'
            f'{_defs(color)}<rect width="320" height="190" fill="{PAPER}"/><ellipse cx="160" cy="176" rx="120" ry="7" fill="{INK}" opacity="0.07"/>{body}</svg>')
