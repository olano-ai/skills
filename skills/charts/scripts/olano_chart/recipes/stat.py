"""stat — the number is the chart.  A hero figure, its label, the takeaway, and an
optional 12-point sparkline (series in the de-emphasis gray, the last point in the
emphasis colour).  Without a series there is nothing for Vega to draw.
"""
from __future__ import annotations

from . import _common as C

SUPPORTS_ANNOTATIONS = False


def has_chart(spec) -> bool:
    return bool(spec.series)


def preferred_height(spec, sc, chart_w):
    return sc.stat_value * 1.1


def build(spec, theme) -> dict:
    sc, box, t = C.sc(spec), C.box(spec), theme.tokens
    s = spec.series[0]
    n = len(spec.categories)
    rows = [{"category": c, "i": i, "value": v, "is_end": i == n - 1, "label": spec.value_format.format(v)}
            for i, (c, v) in enumerate(zip(spec.categories, s.values))]
    x = {"field": "category", "type": "ordinal", "sort": None, "scale": {"type": "point", "padding": 0.05},
         "axis": {"title": None, "values": [spec.categories[0], spec.categories[-1]], "labelColor": t["muted"],
                  "labelFontSize": sc.footer, "domain": False, "ticks": False, "grid": False, "labelFlush": True,
                  "labelAngle": 0, "labelPadding": round(sc.footer * 0.6)}}
    y = {"field": "value", "type": "quantitative", "axis": None, "scale": {"zero": False, "nice": False}}
    gray = theme.context_colors(3)[-1]
    return {"data": {"values": rows}, "layer": [
        {"mark": {"type": "line", "strokeWidth": 2, "strokeJoin": "round", "strokeCap": "round", "color": gray},
         "encoding": {"x": x, "y": y}},
        {"mark": {"type": "point", "filled": True, "size": C.point_area(sc.point_px * 1.3), "stroke": t["surface"], "strokeWidth": 2, "color": t["emphasis"]},
         "transform": [{"filter": "datum.is_end"}], "encoding": {"x": x, "y": y}},
    ], "padding": {"left": 4, "right": round(sc.point_px), "top": round(sc.point_px), "bottom": 0}}
