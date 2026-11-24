"""heatmap — magnitude over a grid, one hue light→dark (flipped on dark surfaces).

Cells carry their value when there is room, in white or ink by the fill's
luminance; a gradient legend sits under the grid.  Rows and columns keep the
order they were given.
"""
from __future__ import annotations

from . import _common as C
from ..palette import label_ink, ramp_color

SUPPORTS_ANNOTATIONS = False


def preferred_height(spec, sc, chart_w):
    cell = chart_w / max(1, len(spec.columns))
    return min(chart_w * 0.9, len(spec.rows) * min(cell, sc.tick * 4.2) + sc.tick * 2.6 + sc.legend * 3.2)


def build(spec, theme) -> dict:
    sc, box, t = C.sc(spec), C.box(spec), theme.tokens
    ramp = list(t["sequential"])
    known = [v for r in spec.matrix for v in r if v is not None]
    vmin, vmax = (min(known), max(known)) if known else (0.0, 1.0)
    if spec.value_axis.min is not None:
        vmin = spec.value_axis.min
    if spec.value_axis.max is not None:
        vmax = spec.value_axis.max
    if vmax <= vmin:
        vmax = vmin + 1
    row_w = min(box.w * 0.28, max(C.measure(spec, theme, r, "body", sc.tick) for r in spec.rows))
    cell_w = (box.w - row_w - sc.tick) / len(spec.columns)
    cell_h = (box.h - sc.tick * 2.2 - sc.legend * 3.2) / len(spec.rows)
    rows = []
    for r, line in zip(spec.rows, spec.matrix):
        for c, v in zip(spec.columns, line):
            label = spec.value_format.format(v) if v is not None else ""
            fill = ramp_color(ramp, (v - vmin) / (vmax - vmin)) if v is not None else t["grid"]
            fits = spec.labels != "none" and v is not None and C.measure(spec, theme, label, "numeric", sc.label) + sc.label * 0.6 <= cell_w and cell_h >= sc.label * 1.5
            rows.append({"row": r, "column": c, "value": v, "label": label if fits else "",
                         "light": label_ink(fill, t["ink"]) != t["ink"]})
    x = {"field": "column", "type": "nominal", "sort": None,
         "axis": C.cat_axis(spec, theme, sc, spec.columns, max_label_w=cell_w * 0.92, highlight=spec.highlight, baseline=False,
                            orient="top", color=t["secondary"], title=spec.x_axis.label or None)}
    y = {"field": "row", "type": "nominal", "sort": None,
         "axis": C.cat_axis(spec, theme, sc, spec.rows, max_label_w=box.w * 0.28, highlight=spec.highlight, baseline=False,
                            title=spec.category_axis.label or None)}
    color = {"field": "value", "type": "quantitative",
             "scale": {"domain": [vmin, vmax], "range": ramp, "interpolate": "rgb"},
             "legend": {"orient": "bottom", "direction": "horizontal", "title": spec.value_axis.label or None,
                        "labelExpr": spec.value_format.axis_expr(), "gradientLength": round(min(box.w * 0.45, sc.legend * 16)),
                        "labelColor": t["muted"], "offset": round(sc.legend * 1.1)}}
    layers = [{"mark": {"type": "rect", "stroke": t["surface"], "strokeWidth": 2},
               "encoding": {"x": x, "y": y, "color": {**color, "condition": {"test": "!isValid(datum.value)", "value": t["grid"]}}}}]
    if spec.labels != "none":
        layers.append({"mark": {"type": "text", "align": "center", "baseline": "middle", **C.font(theme, sc, "numeric", size=round(sc.label * 0.95), weight=400)},
                       "transform": [{"filter": "datum.label != ''"}],
                       "encoding": {"x": x, "y": y, "text": {"field": "label"},
                                    "color": {"condition": {"test": "datum.light", "value": "#ffffff"}, "value": t["ink"]}}})
    return {"data": {"values": rows}, "layer": layers}
