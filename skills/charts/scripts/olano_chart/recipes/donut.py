"""donut — part-to-whole at a glance, at most six slices, labels outside, a hero in the hole.

Slices are separated by a 2px surface gap.  ``highlight`` keeps the named slices
in the emphasis colour and grays the rest.  Labels read "Category" over the
value (or the share with ``percent_of_total``); the hero block sits in the centre.
"""
from __future__ import annotations

from . import _common as C

SUPPORTS_ANNOTATIONS = False
PLACES_HERO = True  # the total sits in the ring; the frame draws no inline hero


def preferred_height(spec, sc, chart_w):
    return chart_w * 0.8


def build(spec, theme) -> dict:
    sc, box, t = C.sc(spec), C.box(spec), theme.tokens
    order = spec.order()
    cats = [spec.categories[i] for i in order]
    vals = [spec.series[0].values[i] or 0 for i in order]
    total = sum(vals) or 1.0
    if spec.highlight:
        colors = [t["emphasis"] if c in spec.highlight else theme.context_colors(len(cats))[k] for k, c in enumerate(cats)]
    else:
        colors = theme.series_colors(len(cats))
    labels_on = spec.labels != "none"
    rows, acc = [], 0.0
    for c, v, col in zip(cats, vals, colors):
        mid = (acc + v / 2) / total
        second = f"{spec.value_format.format(v)} ({100 * v / total:.0f}%)" if spec.percent_of_total else spec.value_format.format(v)
        rows.append({"category": c, "value": v, "mid": mid, "color": col, "lines": [c, second],
                     "lw": max(C.measure(spec, theme, c, "body", sc.tick), C.measure(spec, theme, second, "numeric", sc.label))})
        acc += v
    label_w = (max(r["lw"] for r in rows) + sc.label * 1.0) if labels_on else sc.label * 0.5
    ro = min((box.w - 2 * label_w) / 2, (box.h - 2 * sc.label * 1.7) / 2)
    ro = max(40.0, ro)
    ri = ro * 0.62
    cx, cy = box.w / 2, box.h / 2
    theta = {"field": "value", "type": "quantitative", "stack": True, "sort": None}
    order_enc = {"field": "mid", "type": "quantitative"}
    layers = [{"mark": {"type": "arc", "innerRadius": round(ri), "outerRadius": round(ro), "stroke": t["surface"], "strokeWidth": 2},
               "encoding": {"theta": theta, "order": order_enc,
                            "color": {"field": "color", "type": "nominal", "scale": None, "legend": None}}}]
    if labels_on:
        layers.append({"mark": {"type": "text", "radius": round(ro + sc.label * 0.9), "baseline": "middle", "lineHeight": round(sc.label * 1.3),
                                **C.font(theme, sc, "body", size=sc.tick, weight=400, color=t["ink"]),
                                "align": {"expr": "(datum.mid < 0.03 || datum.mid > 0.97 || abs(datum.mid - 0.5) < 0.03) ? 'center' : (datum.mid < 0.5 ? 'left' : 'right')"}},
                       "encoding": {"theta": theta, "order": order_enc, "text": {"field": "lines"}}})
    if spec.hero is not None:
        hero_role = theme.frame.get("hero_font", "numeric")
        hv = min(sc.hero_value, ri * 0.9)
        dy_v = -round(sc.hero_label * 0.55) if spec.hero.label else 0
        layers.append({"mark": {"type": "text", "align": "center", "baseline": "middle", "dy": dy_v,
                                **C.font(theme, sc, hero_role, size=round(hv), color=t["ink"])},
                       "encoding": {"x": {"value": cx}, "y": {"value": cy}, "text": {"value": spec.hero.value}}})
        if spec.hero.label:
            layers.append({"mark": {"type": "text", "align": "center", "baseline": "middle", "dy": round(hv * 0.55),
                                    **C.font(theme, sc, "body", size=sc.hero_label * 0.8, weight=400, color=t["secondary"])},
                           "encoding": {"x": {"value": cx}, "y": {"value": cy}, "text": {"value": spec.hero.label}}})
    return {"data": {"values": rows}, "layer": layers}
