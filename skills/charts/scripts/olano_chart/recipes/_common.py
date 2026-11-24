"""Helpers shared by the recipes.  A recipe stays readable by leaning on these."""
from __future__ import annotations

import json

from ..palette import label_ink, steps, validate_ordinal


def sc(spec):
    return spec.layout.scale


def box(spec):
    return spec.layout.chart


def measure(spec, theme, text: str, role: str = "body", size: float | None = None,
            weight: int | None = None, style: str | None = None) -> float:
    """Pixel width of ``text`` in one of the theme's font roles (unkerned, so slightly generous)."""
    s = spec.layout.scale
    return spec.measurer.width(str(text), theme.family(role), size or s.tick,
                               theme.weight(role) if weight is None else weight,
                               style or theme.style(role))


def font(theme, scale, role: str = "numeric", size: float | None = None, weight: int | None = None,
         color: str | None = None, style: str | None = None) -> dict:
    """Vega text-mark font properties for a role.  Text is always an ink token, never a series colour."""
    d = {"font": theme.stack(role), "fontSize": size or scale.label,
         "fontWeight": theme.weight(role) if weight is None else weight}
    st = style or theme.style(role)
    if st != "normal":
        d["fontStyle"] = st
    d["color"] = color or theme.tokens["ink"]
    return d


def category_colors(spec, theme, cats: list[str]) -> list[str]:
    """Colours for a single series' categories: one hue, unless highlighted or ordinal."""
    t = theme.tokens
    if spec.highlight:
        return [t["emphasis"] if c in spec.highlight else t["deemphasis"] for c in cats]
    if spec.ordinal:
        ramp = steps(t["ordinal"], len(cats))
        if len(ramp) > 1:
            _, ok = validate_ordinal(ramp, theme.mode, t["surface"])
            if not ok:
                raise ValueError("the theme's ordinal ramp does not validate at this step count — use fewer categories or a categorical series")
        return ramp
    return [t["categorical"][0]] * len(cats)


def series_colors(spec, theme) -> dict[str, str]:
    """Colour per series name: fixed slots in order, or emphasis + de-emphasis grays when a role/highlight says so."""
    t = theme.tokens
    names = [s.name for s in spec.series]
    emph = [n for n in names if n in spec.emphasis_series() or n in spec.highlight]
    if not emph:
        return dict(zip(names, theme.series_colors(len(names))))
    out: dict[str, str] = {}
    slot = 1
    grays = theme.context_colors(len(names))
    gi = 0
    for n in names:
        if n in emph:
            if n == emph[0]:
                out[n] = t["emphasis"]
            else:
                out[n] = t["categorical"][slot % 8]
                slot += 1
        else:
            out[n] = grays[gi]
            gi += 1
    return out


def wrap_expr(labels: list[str], max_w: float, spec, theme, role: str = "body", size: float | None = None,
              weight: int = 400, max_lines: int = 2) -> str | None:
    """A Vega ``labelExpr`` that wraps long axis labels onto two lines; ``None`` when all fit."""
    s = spec.layout.scale
    size = size or s.tick
    wrapped: list[list[str]] = []
    need = False
    for lab in labels:
        lines = spec.measurer.wrap(lab, max_w, theme.family(role), size, weight, "normal", max_lines=max_lines)
        wrapped.append(lines)
        need = need or len(lines) > 1 or lines[0] != lab
    if not need:
        return None
    keys = json.dumps(labels, ensure_ascii=False)
    vals = json.dumps(wrapped, ensure_ascii=False)
    return f"indexof({keys}, datum.value) >= 0 ? {vals}[indexof({keys}, datum.value)] : datum.label"


def cat_axis(spec, theme, scale, labels: list[str], *, max_label_w: float, highlight=(), baseline: bool = True,
             title: str | None = None, orient: str | None = None, wrap: bool = True, color: str | None = None) -> dict:
    """The category axis: ink labels, no ticks, an optional baseline, highlighted names in bold."""
    t = theme.tokens
    ax: dict = {"title": title, "labelColor": color or t["ink"], "labelFontSize": scale.tick, "labelPadding": round(scale.tick * 0.7),
                "domain": baseline, "domainColor": t["baseline"], "ticks": False, "grid": False,
                "labelAngle": 0, "labelLimit": 0, "labelOverlap": False}
    if orient:
        ax["orient"] = orient
    if wrap:
        expr = wrap_expr(labels, max_label_w, spec, theme, "body", scale.tick)
        if expr:
            ax["labelExpr"] = expr
    if highlight:
        ax["labelFontWeight"] = {"condition": {"test": f"indexof({json.dumps(list(highlight), ensure_ascii=False)}, datum.value) >= 0", "value": 700}, "value": 400}
    return ax


def value_axis(spec, theme, scale, *, grid: bool = True, title: str | None = None, orient: str | None = None,
               tick_count: int = 5, fmt=None) -> dict:
    """The value axis: muted ticks formatted like the labels, hairline grid, no domain line."""
    vf = fmt or spec.value_format
    ax = {"title": title, "grid": grid, "labelExpr": vf.axis_expr(), "tickCount": tick_count, "domain": False,
          "ticks": False, "labelFlush": True}
    if orient:
        ax["orient"] = orient
    return ax


def extend_domain(lo: float, hi: float, plot_px: float, gutter_px: float) -> float:
    """Stretch ``hi`` so ``gutter_px`` of plot stays free past the longest mark (for labels)."""
    usable = max(1.0, plot_px - gutter_px)
    return hi + (hi - lo) * (gutter_px / usable)


def domain_bounds(spec, values: list[float | None], *, zero: bool = True) -> tuple[float, float, bool]:
    """(lo, hi, hi_is_fixed) honouring value_axis.min/max."""
    known = [v for v in values if v is not None]
    vmin, vmax = (min(known), max(known)) if known else (0.0, 1.0)
    lo = spec.value_axis.min if spec.value_axis.min is not None else (min(0.0, vmin) if zero else vmin)
    hi = spec.value_axis.max if spec.value_axis.max is not None else max(vmax, lo + 1e-9)
    if hi <= lo:
        hi = lo + 1.0
    return lo, hi, spec.value_axis.max is not None


def inside_ink(theme, fill: str) -> str:
    return label_ink(fill, theme.tokens["ink"])


def legend_for(names: list[str], colors: dict[str, str]) -> dict:
    return {"field": "series", "type": "nominal", "sort": None,
            "scale": {"domain": names, "range": [colors[n] for n in names]},
            "legend": {"values": names}}


def point_area(diameter_px: float) -> float:
    return round(0.785 * diameter_px * diameter_px, 1)


def filter_eq(field: str, value) -> dict:
    return {"filter": {"field": field, "equal": value}}
