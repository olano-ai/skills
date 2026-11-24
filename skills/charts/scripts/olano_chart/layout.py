"""Size presets, the type scale per preset, chrome geometry and the label-fit numbers.

Everything is computed in CSS pixels at the card's logical size (the PNG is
rendered at 2×).  The chrome — kicker, title, subtitle, hero, captions, footer,
logo, rules — is laid out here, in Python, from measured text, so the HTML page
and the optional SVG card place every element at the same coordinates.  Vega
gets the remaining rectangle (``Layout.chart``) and fits itself inside it.
"""
from __future__ import annotations

import base64
import re
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .fonts import Measurer

PRESETS: dict[str, tuple[int, int]] = {
    "square": (1200, 1200),     # LinkedIn / Instagram feed, chat
    "landscape": (1200, 675),   # X, LinkedIn link card, chat
    "portrait": (1080, 1350),   # Instagram / LinkedIn 4:5
    "story": (1080, 1920),      # Stories / Reels / TikTok
    "slide": (1920, 1080),      # 16:9 deck
    "email": (1200, 600),       # newsletter hero
    "report": (1600, 900),      # document figure
}
SIZE_MIN, SIZE_MAX = 320, 4000
BAR_CAP_BASE = 24.0  # px at a 16px tick size; scales with the type scale


def parse_size(text: str | None) -> tuple[str, int, int]:
    """``square`` → (square, 1200, 1200); ``1400x900`` → (custom, 1400, 900)."""
    s = (text or "square").strip().lower()
    if s in PRESETS:
        w, h = PRESETS[s]
        return s, w, h
    m = re.fullmatch(r"(\d{3,4})\s*[x×]\s*(\d{3,4})", s)
    if not m:
        raise ValueError(f"size must be a preset ({', '.join(PRESETS)}) or WxH like 1400x900 (got '{text}')")
    w, h = int(m.group(1)), int(m.group(2))
    for v in (w, h):
        if not SIZE_MIN <= v <= SIZE_MAX:
            raise ValueError(f"custom sizes must be between {SIZE_MIN} and {SIZE_MAX} px on each side (got {w}x{h})")
    return "custom", w, h


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


@dataclass
class TypeScale:
    """Font sizes (px) for one card; everything else in the layout derives from these."""
    title: int
    subtitle: int
    kicker: int
    tick: int
    label: int
    legend: int
    footer: int
    annotation: int
    caption: int
    hero_value: int
    hero_label: int
    stat_value: int
    bar_cap: int         # max bar thickness
    point_px: int        # marker diameter
    row_step_max: int    # max distance between bar rows before the chart stops growing


def type_scale(w: int, h: int, frame: dict | None = None) -> TypeScale:
    frame = frame or {}
    short = min(w, h)
    title = _clamp(0.024 * w + 0.018 * h, 28, 84) * float(frame.get("title_scale", 1.0))
    tick = max(12.0, title * 0.36)
    numeric_scale = float(frame.get("numeric_scale", 1.0))
    bar_cap = round(BAR_CAP_BASE * tick / 16.0)
    return TypeScale(
        title=round(title),
        subtitle=round(max(13, title * 0.48)),
        kicker=round(max(12, title * 0.30)),
        tick=round(tick),
        label=round(max(12, title * 0.37 * numeric_scale)),
        legend=round(max(12, title * 0.35)),
        footer=round(max(11, title * 0.29)),
        annotation=round(max(12, title * 0.36 * float(frame.get("annotation_scale", 1.0)))),
        caption=round(max(12, title * 0.33)),
        hero_value=round(title * 1.7 * numeric_scale),
        hero_label=round(max(13, title * 0.48)),
        stat_value=round(_clamp(short * 0.17, 72, 320) * numeric_scale),
        bar_cap=bar_cap,
        point_px=max(8, round(tick * 0.5)),
        row_step_max=round(bar_cap * 2.6),
    )


@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h

    def as_dict(self) -> dict:
        return {"x": round(self.x, 2), "y": round(self.y, 2), "w": round(self.w, 2), "h": round(self.h, 2)}


@dataclass
class TextBlock:
    role: str
    lines: list[str]
    x: float
    y: float
    w: float
    size: float
    line_height: float
    family: str          # CSS family name (bare)
    stack: str           # CSS font-family stack
    weight: int
    style: str
    color: str
    align: str = "left"
    letter_spacing_em: float = 0.0
    uppercase: bool = False
    baselines: list[float] = field(default_factory=list)  # y of each line's baseline (for SVG)

    @property
    def h(self) -> float:
        return self.line_height * len(self.lines)

    @property
    def bottom(self) -> float:
        return self.y + self.h

    def as_dict(self) -> dict:
        return {"role": self.role, "lines": self.lines, "x": round(self.x, 2), "y": round(self.y, 2), "w": round(self.w, 2),
                "size": self.size, "lineHeight": round(self.line_height, 2), "family": self.family, "stack": self.stack,
                "weight": self.weight, "style": self.style, "color": self.color, "align": self.align,
                "letterSpacing": self.letter_spacing_em, "uppercase": self.uppercase,
                "baselines": [round(b, 2) for b in self.baselines]}


@dataclass
class Rule:
    x1: float
    y1: float
    x2: float
    y2: float
    color: str
    width: float = 1.0

    def as_dict(self) -> dict:
        return {"x1": self.x1, "y1": self.y1, "x2": self.x2, "y2": self.y2, "color": self.color, "width": self.width}


@dataclass
class Logo:
    box: Box
    data_uri: str

    def as_dict(self) -> dict:
        return {**self.box.as_dict(), "href": self.data_uri}


@dataclass
class Layout:
    preset: str
    width: int
    height: int
    margin: int
    scale: TypeScale
    blocks: list[TextBlock] = field(default_factory=list)
    rules: list[Rule] = field(default_factory=list)
    chart: Box | None = None
    logo: Logo | None = None
    content_x: float = 0
    content_w: float = 0

    def block(self, role: str) -> TextBlock | None:
        return next((b for b in self.blocks if b.role == role), None)

    def as_dict(self) -> dict:
        return {"width": self.width, "height": self.height, "margin": self.margin,
                "blocks": [b.as_dict() for b in self.blocks], "rules": [r.as_dict() for r in self.rules],
                "chart": self.chart.as_dict() if self.chart else None, "logo": self.logo.as_dict() if self.logo else None}


def margins(w: int, h: int, preset: str) -> tuple[int, int, int]:
    """(side, top, bottom) margins — ≥ 6% of the short side; stories keep out of the platform UI bands."""
    short, long_ = min(w, h), max(w, h)
    m = round(max(0.06 * short, 0.045 * long_))
    if preset == "story":
        return m, max(m, round(0.11 * h)), max(m, round(0.16 * h))
    return m, m, m


# ---------------------------------------------------------------------------
# images (logo)
# ---------------------------------------------------------------------------
def image_info(path: Path) -> tuple[str, float, float, str]:
    """(mime, width, height, data URI) for png/jpeg/gif/webp/svg; size falls back to 3:1."""
    data = path.read_bytes()
    ext = path.suffix.lower()
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
            ".webp": "image/webp", ".svg": "image/svg+xml"}.get(ext, "application/octet-stream")
    w = h = 0.0
    try:
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            w, h = struct.unpack(">II", data[16:24])
        elif data[:3] == b"\xff\xd8\xff":
            i = 2
            while i < len(data) - 9:
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i + 1]
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    h, w = struct.unpack(">HH", data[i + 5 : i + 9])
                    break
                (seglen,) = struct.unpack(">H", data[i + 2 : i + 4])
                i += 2 + seglen
        elif data[:6] in (b"GIF87a", b"GIF89a"):
            w, h = struct.unpack("<HH", data[6:10])
        elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            chunk = data[12:16]
            if chunk == b"VP8X":
                w = 1 + int.from_bytes(data[24:27], "little")
                h = 1 + int.from_bytes(data[27:30], "little")
            elif chunk == b"VP8L":
                b = int.from_bytes(data[21:25], "little")
                w, h = (b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1
            elif chunk == b"VP8 ":
                w, h = struct.unpack("<HH", data[26:30])
                w, h = w & 0x3FFF, h & 0x3FFF
        elif mime == "image/svg+xml" or b"<svg" in data[:2000]:
            mime = "image/svg+xml"
            head = data[:4000].decode("utf-8", "ignore")
            m = re.search(r"viewBox=[\"']\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)", head)
            if m:
                w, h = float(m.group(1)), float(m.group(2))
            else:
                mw = re.search(r"<svg[^>]*\swidth=[\"']([\d.]+)", head)
                mh = re.search(r"<svg[^>]*\sheight=[\"']([\d.]+)", head)
                if mw and mh:
                    w, h = float(mw.group(1)), float(mh.group(1))
    except Exception:
        w = h = 0.0
    if not w or not h:
        w, h = 3.0, 1.0
    return mime, float(w), float(h), f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


# ---------------------------------------------------------------------------
# the layout itself
# ---------------------------------------------------------------------------
def compute_layout(spec, theme, size: str, measurer: Measurer, *, supports_annotations: bool = True,
                   preferred_height=None, has_chart: bool = True, cwd: Path | None = None,
                   places_hero: bool = False) -> Layout:
    """Lay out the chrome for ``spec`` on ``size`` and hand Vega the rest.

    ``preferred_height(spec, scale, chart_w) -> float | None`` lets a recipe cap
    the chart (five bars do not want 800px); the leftover becomes air above the
    footer, or — on tall cards — centres the whole block.
    """
    preset, W, H = parse_size(size)
    frame = theme.frame
    sc = type_scale(W, H, frame)
    m_side, m_top, m_bottom = margins(W, H, preset)
    t = theme.tokens
    lay = Layout(preset, W, H, m_side, sc)
    x0, cw = m_side, W - 2 * m_side
    lay.content_x, lay.content_w = x0, cw
    is_stat = spec.type == "stat"

    def block(role, text, size, family_role, weight, style, color, *, lh=1.25, max_lines=None, y=0.0, w=cw,
              x=x0, align="left", tracking=0.0, upper=False, shrink_to_lines=None) -> TextBlock:
        family = theme.family(family_role)
        stack = theme.stack(family_role)
        txt = text.upper() if upper else text
        size_ = float(size)
        lines = measurer.wrap(txt, w, family, size_, weight, style, tracking)
        if shrink_to_lines:
            while len(lines) > shrink_to_lines and size_ > size * 0.68:
                size_ = round(size_ * 0.92)
                lines = measurer.wrap(txt, w, family, size_, weight, style, tracking)
        if max_lines:
            lines = measurer.wrap(txt, w, family, size_, weight, style, tracking, max_lines=max_lines)
        line_h = round(size_ * lh, 2)
        blk = TextBlock(role, lines, x, y, w, size_, line_h, family, stack, weight, style, color, align, tracking, upper)
        asc, desc = measurer.metrics(family, weight, style)
        for i in range(len(lines)):
            top = y + i * line_h
            blk.baselines.append(round(top + (line_h - (asc + desc) * size_) / 2 + asc * size_, 2))
        return blk

    # ---- footer first: it is pinned to the bottom -------------------------
    footer_blocks: list[TextBlock] = []
    logo: Logo | None = None
    footer_w = cw
    if spec.logo:
        lp = Path(spec.logo)
        if not lp.is_absolute():
            lp = (cwd or Path.cwd()) / lp
        if lp.is_file():
            mime, iw, ih, uri = image_info(lp)
            lh_ = _clamp(sc.footer * 2.6, 24, 72)
            lw_ = lh_ * iw / ih
            if lw_ > cw * 0.3:
                lw_ = cw * 0.3
                lh_ = lw_ * ih / iw
            logo = Logo(Box(x0 + cw - lw_, H - m_bottom - lh_, lw_, lh_), uri)
            footer_w = cw - lw_ - sc.footer * 2
        else:
            print(f"note: logo file not found, skipping: {lp}", file=sys.stderr)
    src_line = spec.notes.source_line
    note = spec.notes.note
    body_fam, body_w = theme.family("body"), 400
    f_lh = 1.4
    if src_line and note and logo is None:
        sw = measurer.width(src_line, body_fam, sc.footer, body_w)
        nw = measurer.width(note, body_fam, sc.footer, body_w)
        if sw + sc.footer * 2 + nw <= footer_w:
            b1 = block("source", src_line, sc.footer, "body", body_w, "normal", t["muted"], lh=f_lh, max_lines=1, w=footer_w)
            b2 = block("note", note, sc.footer, "body", body_w, "normal", t["muted"], lh=f_lh, max_lines=1, w=footer_w, align="right")
            footer_blocks = [b1, b2]
    if not footer_blocks:
        if src_line:
            footer_blocks.append(block("source", src_line, sc.footer, "body", body_w, "normal", t["muted"], lh=f_lh, max_lines=2, w=footer_w))
        if note:
            footer_blocks.append(block("note", note, sc.footer, "body", body_w, "normal", t["muted"], lh=f_lh, max_lines=3, w=footer_w))
    footer_h = 0.0
    if footer_blocks:
        same_line = len(footer_blocks) == 2 and footer_blocks[1].align == "right"
        footer_h = footer_blocks[0].h if same_line else sum(b.h for b in footer_blocks) + (sc.footer * 0.25 if len(footer_blocks) > 1 else 0)
    footer_top = H - m_bottom - footer_h
    if logo is not None and logo.box.h > footer_h:
        footer_top = H - m_bottom - logo.box.h + (logo.box.h - footer_h) / 2  # vertically centre text on the logo
    # place footer lines
    yy = footer_top
    for i, b in enumerate(footer_blocks):
        same_line = len(footer_blocks) == 2 and footer_blocks[1].align == "right"
        b_y = footer_top if (same_line or i == 0) else yy
        _reposition(b, b_y)
        if not same_line:
            yy = b.bottom + sc.footer * 0.25
    footer_region_top = min([footer_top] + ([logo.box.y] if logo else []))

    # ---- chrome from the top -----------------------------------------------
    blocks: list[TextBlock] = []
    y = float(m_top)
    rules: list[Rule] = []
    if frame.get("rules"):
        rules.append(Rule(x0, y, x0 + cw, y, t["rule"], 1.0))
        y += sc.kicker * 1.1
    if spec.kicker:
        kb = block("kicker", spec.kicker, sc.kicker, "body", int(frame.get("kicker_weight", 700)), "normal", t["secondary"],
                   lh=1.2, max_lines=1, y=y, tracking=_em(frame.get("kicker_tracking", "0.12em")), upper=True)
        blocks.append(kb)
        y = kb.bottom + sc.kicker * 0.9
    if is_stat:
        y = _stat_block(spec, theme, sc, block, blocks, y, measurer, t)
    else:
        tb = block("title", spec.title, sc.title, "display", theme.weight("display"), theme.style("display"), t["ink"],
                   lh=1.08 if theme.font("display").get("generic") != "serif" else 1.04, y=y,
                   tracking=_em(frame.get("title_tracking", "0")), shrink_to_lines=3, max_lines=3)
        blocks.append(tb)
        y = tb.bottom + sc.subtitle * 0.55
        if spec.subtitle:
            sb = block("subtitle", spec.subtitle, sc.subtitle, "body", 400, "normal", t["secondary"], lh=1.3, y=y, max_lines=2)
            blocks.append(sb)
            y = sb.bottom
        if spec.hero is not None and not places_hero:
            y += sc.subtitle * 0.9
            y = _inline_hero(spec, theme, sc, block, blocks, y, measurer, t)
        y += sc.subtitle * 1.15

    # captions: annotations the chart form cannot place beside a mark
    caption_blocks: list[TextBlock] = []
    if spec.annotations and not supports_annotations:
        for a in spec.annotations:
            cb = block("caption", f"{a.target} — {a.text}", sc.caption, "annotation", theme.weight("annotation"),
                       theme.style("annotation"), t["secondary"], lh=1.4, max_lines=2, w=cw - sc.caption * 1.6, x=x0 + sc.caption * 1.6)
            caption_blocks.append(cb)
    captions_h = sum(b.h for b in caption_blocks) + (sc.caption * 0.5 * max(0, len(caption_blocks) - 1))

    # chart box
    chart_top = y
    gap_footer = sc.footer * 1.8
    chart_bottom = footer_region_top - gap_footer - (captions_h + sc.caption * 1.2 if caption_blocks else 0)
    if frame.get("rules"):
        chart_bottom -= sc.footer * 0.9
    available = max(120.0, chart_bottom - chart_top)
    chart_h = available
    chart_w = cw
    if is_stat and has_chart:
        chart_h = min(available, max(90.0, H * 0.18))
    elif has_chart and preferred_height is not None:
        pref = preferred_height(spec, sc, chart_w)
        if pref:
            chart_h = _clamp(pref, min(available, 160.0), available)
    chart_h = round(chart_h)
    leftover = available - chart_h
    if not has_chart:
        chart_h, leftover = 0, available

    # Tall-ish cards (square, portrait, story): a capped chart would leave a dead band above the
    # footer.  Let the chart grow up to 1.5× its preferred height, then centre it in what is left —
    # the title stays at the top and the footer stays pinned.  A stat card centres its whole block.
    tallish = H >= 0.9 * W and has_chart and not is_stat
    if tallish and leftover > 0.15 * available:
        grow = min(leftover, chart_h * 0.6)
        chart_h += round(grow)
        leftover = available - chart_h
    if tallish and leftover > 0.15 * available:
        chart_top += round(leftover * 0.4)  # a little more air below than above
        leftover = 0
    shift = round(leftover / 2) if (is_stat and leftover > 0) else 0
    if shift:
        for b in blocks:
            _reposition(b, b.y + shift)
        for r in rules:
            r.y1 += shift
            r.y2 += shift
        chart_top += shift
    lay.chart = Box(x0, chart_top, chart_w, chart_h) if has_chart else None
    cap_y = (chart_top + chart_h + sc.caption * 1.2) if has_chart else chart_top
    for cb in caption_blocks:
        _reposition(cb, cap_y)
        cap_y = cb.bottom + sc.caption * 0.5
    blocks.extend(caption_blocks)
    if frame.get("rules") and (footer_blocks or logo):
        rules.append(Rule(x0, footer_region_top - sc.footer * 0.9, x0 + cw, footer_region_top - sc.footer * 0.9, t["grid"], 1.0))
    blocks.extend(footer_blocks)
    lay.blocks = blocks
    lay.rules = rules
    lay.logo = logo
    return lay


def _em(v) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if s.endswith("em"):
        return float(s[:-2])
    try:
        return float(s)
    except ValueError:
        return 0.0


def _reposition(b: TextBlock, new_y: float) -> None:
    dy = new_y - b.y
    b.y = new_y
    b.baselines = [round(v + dy, 2) for v in b.baselines]


def _inline_hero(spec, theme, sc, block, blocks, y, measurer, t) -> float:
    hero_role = theme.frame.get("hero_font", "numeric")
    hv = block("hero_value", spec.hero.value, sc.hero_value, hero_role, theme.weight(hero_role), "normal", t["ink"],
               lh=1.05, max_lines=1, y=y, tracking=_em(theme.frame.get("hero_tracking", "-0.02em")))
    blocks.append(hv)
    vw = measurer.width(spec.hero.value, theme.family(hero_role), sc.hero_value, theme.weight(hero_role), "normal", hv.letter_spacing_em)
    x_label = hv.x + vw + sc.hero_label * 0.6
    if spec.hero.label:
        hl = block("hero_label", spec.hero.label, sc.hero_label, "body", 400, "normal", t["secondary"], lh=1.05, max_lines=1,
                   x=x_label, w=max(80.0, hv.x + hv.w - x_label))
        # baseline-align the label with the big number
        _reposition(hl, hv.baselines[0] - (hl.baselines[0] - hl.y))
        blocks.append(hl)
        x_label += measurer.width(spec.hero.label, theme.family("body"), sc.hero_label) + sc.hero_label * 0.7
    if spec.hero.delta:
        neg = spec.hero.delta.strip()[:1] in ("-", "−", "↓")
        hd = block("hero_delta", spec.hero.delta, sc.hero_label, "body", 700, "normal", t["negative"] if neg else t["positive"],
                   lh=1.05, max_lines=1, x=x_label, w=max(60.0, hv.x + hv.w - x_label))
        _reposition(hd, hv.baselines[0] - (hd.baselines[0] - hd.y))
        blocks.append(hd)
    return hv.bottom


def _stat_block(spec, theme, sc, block, blocks, y, measurer, t) -> float:
    hero_role = theme.frame.get("hero_font", "numeric")
    hv = block("hero_value", spec.hero.value, sc.stat_value, hero_role, theme.weight(hero_role), "normal", t["ink"],
               lh=1.0, max_lines=1, y=y, tracking=_em(theme.frame.get("hero_tracking", "-0.02em")), shrink_to_lines=1)
    blocks.append(hv)
    y = hv.bottom + sc.subtitle * 0.35
    if spec.hero.delta:
        neg = spec.hero.delta.strip()[:1] in ("-", "−", "↓")
        hd = block("hero_delta", spec.hero.delta, sc.subtitle, "body", 700, "normal", t["negative"] if neg else t["positive"],
                   lh=1.3, max_lines=1, y=y)
        blocks.append(hd)
        y = hd.bottom + sc.subtitle * 0.2
    if spec.hero.label:
        hl = block("hero_label", spec.hero.label, sc.hero_label, "body", 400, "normal", t["secondary"], lh=1.3, max_lines=2, y=y)
        blocks.append(hl)
        y = hl.bottom
    y += sc.subtitle * 1.2
    tb = block("title", spec.title, round(sc.title * 0.74), "display", theme.weight("display"), theme.style("display"), t["ink"],
               lh=1.12, y=y, tracking=_em(theme.frame.get("title_tracking", "0")), shrink_to_lines=3, max_lines=3)
    blocks.append(tb)
    y = tb.bottom + sc.subtitle * 0.45
    if spec.subtitle:
        sb = block("subtitle", spec.subtitle, sc.subtitle, "body", 400, "normal", t["secondary"], lh=1.3, y=y, max_lines=2)
        blocks.append(sb)
        y = sb.bottom
    return y + sc.subtitle * 1.2
