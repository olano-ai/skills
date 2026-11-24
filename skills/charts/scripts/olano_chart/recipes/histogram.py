"""histogram — the distribution of raw observations.  Binning happens here (nice
bin widths of 1/2/2.5/5 × 10ⁿ near the requested count) so labels and axes are
deterministic; bars touch with a 2px surface gap.  ``x_axis.label`` names the unit.
"""
from __future__ import annotations

import math

from . import _common as C

SUPPORTS_ANNOTATIONS = False


def preferred_height(spec, sc, chart_w):
    return chart_w * 0.55


def nice_bins(values: list[float], bins: int) -> tuple[list[float], list[int]]:
    lo, hi = min(values), max(values)
    span = (hi - lo) or abs(hi) or 1.0
    raw = span / max(1, bins)
    mag = 10 ** math.floor(math.log10(raw))
    width = next(m * mag for m in (1, 2, 2.5, 5, 10) if raw <= m * mag)
    start = math.floor(lo / width) * width
    edges = [start]
    while edges[-1] < hi or len(edges) < 2:
        edges.append(round(edges[-1] + width, 10))
    counts = [0] * (len(edges) - 1)
    for v in values:
        k = min(int((v - start) / width), len(counts) - 1)
        counts[k] += 1
    return edges, counts


def build(spec, theme) -> dict:
    sc, box, t = C.sc(spec), C.box(spec), theme.tokens
    edges, counts = nice_bins(spec.values, spec.bins)
    n = len(counts)
    labels_on = spec.labels == "all" or (spec.labels in ("auto", "extremes", "ends") and n <= 12)
    rows = [{"x0": edges[k], "x1": edges[k + 1], "mid": (edges[k] + edges[k + 1]) / 2, "count": counts[k],
             "label": f"{counts[k]:,}"} for k in range(n)]
    plot_h = box.h - sc.tick * 2.6
    hi = max(counts) or 1
    top = hi * (1 + (sc.label * 1.3) / plot_h) if labels_on else hi
    every = max(1, math.ceil(n / 8))
    tick_values = [e for k, e in enumerate(edges) if k % every == 0] + ([edges[-1]] if (n % every) else [])
    count_axis = C.value_axis(spec, theme, sc, title=spec.value_axis.label or "Count", fmt=_CountFormat())
    x = {"field": "x0", "type": "quantitative", "scale": {"domain": [edges[0], edges[-1]], "nice": False, "zero": False},
         "axis": {"title": spec.x_axis.label or None, "values": tick_values, "labelExpr": spec.value_format.axis_expr(),
                  "domain": True, "domainColor": t["baseline"], "grid": False, "ticks": False, "labelFlush": True,
                  "labelPadding": round(sc.tick * 0.7)}}
    y = {"field": "count", "type": "quantitative", "scale": {"domain": [0, top], "nice": not labels_on, "zero": True},
         "axis": None if labels_on else count_axis}
    layers = [{"mark": {"type": "bar", "cornerRadiusEnd": 2, "stroke": t["surface"], "strokeWidth": 2},
               "encoding": {"x": x, "x2": {"field": "x1"}, "y": y, "y2": {"datum": 0}, "color": {"value": t["categorical"][0]}}}]
    if labels_on:
        layers.append({"mark": {"type": "text", "align": "center", "baseline": "bottom", "dy": -round(sc.label * 0.35), **C.font(theme, sc, "numeric", size=round(sc.label * 0.9))},
                       "encoding": {"x": {"field": "mid", "type": "quantitative"}, "y": y, "text": {"field": "label"},
                                    "color": {"value": t["secondary"]}}})
    return {"data": {"values": rows}, "layer": layers}


class _CountFormat:
    def axis_expr(self) -> str:
        return "format(datum.value, ',~f')"
