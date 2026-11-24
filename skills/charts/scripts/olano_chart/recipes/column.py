"""column — vertical bars for a single series (short category names, or a natural left→right order).

Same rules as ``bar``: one hue, emphasis via ``highlight``, ordinal ramp on request,
values on the cap, and the value axis hidden once every column is labelled.
"""
from __future__ import annotations

from . import _common as C

SUPPORTS_ANNOTATIONS = True


def preferred_height(spec, sc, chart_w):
    return chart_w * 0.62


def build(spec, theme) -> dict:
    sc, box, t = C.sc(spec), C.box(spec), theme.tokens
    order = spec.order()
    cats = [spec.categories[i] for i in order]
    vals = [spec.series[0].values[i] for i in order]
    n = len(cats)
    colors = C.category_colors(spec, theme, cats)
    labels_on = spec.labels != "none"
    texts = [spec.label_for(v) for v in vals]

    axis_w = 0 if labels_on else sc.tick * 3.2
    plot_w = box.w - axis_w
    step = plot_w / n
    bar_w = min(sc.bar_cap * 1.5, step * 0.62)
    plot_h = box.h - sc.tick * 2.6
    lo, hi, hi_fixed = C.domain_bounds(spec, vals)
    ann = {a.target: a for a in spec.annotations if a.target in cats}
    if not hi_fixed:
        room = (sc.label * 1.3 if labels_on else 0) + (sc.annotation * 1.5 if ann else 0)
        if room:
            hi = C.extend_domain(lo, hi, plot_h, room)

    rows = []
    for i, c in enumerate(cats):
        strong = (not spec.highlight) or (c in spec.highlight)
        rows.append({"category": c, "value": vals[i], "label": texts[i], "color": colors[i],
                     "lbl": t["ink"] if strong else t["secondary"], "lblw": 700 if strong else 400})
    x = {"field": "category", "type": "nominal", "sort": None,
         "axis": C.cat_axis(spec, theme, sc, cats, max_label_w=step * 0.92, highlight=spec.highlight,
                            title=spec.category_axis.label or None),
         "scale": {"paddingInner": 0.3, "paddingOuter": 0.15}}
    y = {"field": "value", "type": "quantitative", "scale": {"domain": [lo, hi], "nice": False, "zero": False},
         "axis": None if labels_on else C.value_axis(spec, theme, sc, title=spec.value_axis.label or None)}
    layers = [{"mark": {"type": "bar", "width": round(bar_w, 1), "cornerRadiusEnd": 4},
               "encoding": {"x": x, "y": y, "color": {"field": "color", "type": "nominal", "scale": None, "legend": None}}}]
    if labels_on:
        layers.append({"mark": {"type": "text", "align": "center", "baseline": "bottom", "dy": -round(sc.label * 0.4),
                                **C.font(theme, sc, "numeric"), "fontWeight": {"expr": "datum.lblw"}},
                       "encoding": {"x": x, "y": y, "text": {"field": "label"},
                                    "color": {"field": "lbl", "type": "nominal", "scale": None, "legend": None}}})
    for c, a in ann.items():
        dy = -round(sc.label * 0.4 + (sc.label * 1.35 if labels_on else 0) + sc.annotation * 0.35)
        idx = cats.index(c)
        left_taller = idx > 0 and (vals[idx - 1] or 0) > (vals[idx] or 0)
        right_taller = idx < n - 1 and (vals[idx + 1] or 0) > (vals[idx] or 0)
        if left_taller and right_taller or (left_taller and idx > 2 * n / 3) or (right_taller and idx < n / 3):
            align = "center"  # over its own column, never drifting across a taller neighbour
        else:
            align = "left" if idx < n / 3 and n > 2 else ("right" if idx > 2 * n / 3 and n > 2 else "center")
        layers.append({"mark": {"type": "text", "align": align, "baseline": "bottom", "dy": dy,
                                **C.font(theme, sc, "annotation", size=sc.annotation, color=t["secondary"])},
                       "transform": [C.filter_eq("category", c)],
                       "encoding": {"x": x, "y": y, "text": {"value": a.text}}})
    out = {"data": {"values": rows}, "layer": layers}
    centred = [a for c, a in ann.items() if cats.index(c) >= n - 2]
    if centred:  # residual of autosize fit for text centred over the last columns
        widest = max(C.measure(spec, theme, a.text, "annotation", sc.annotation) for a in centred)
        out["padding"] = {"right": round(0.2 * widest / 2 + 4)}
    return out
