"""dumbbell — before → after per category: two dots joined by a rule, one hue in two shades.

The second series is "after" and takes slot 1; "before" takes a lighter step of
the same hue.  Values sit outside their own dot on the far side, so the change
reads left to right.  Sorted by the after value unless ``sort`` says otherwise.
"""
from __future__ import annotations

from . import _common as C

SUPPORTS_ANNOTATIONS = True


def preferred_height(spec, sc, chart_w):
    return len(spec.categories) * sc.row_step_max + sc.legend * 2.6 + sc.tick * 0.6


def build(spec, theme) -> dict:
    sc, box, t = C.sc(spec), C.box(spec), theme.tokens
    order = spec.order()
    cats = [spec.categories[i] for i in order]
    before, after = spec.series
    ramp = t.get("ordinal") or [t["categorical"][0]]
    c_before = ramp[1] if theme.mode == "light" and len(ramp) > 1 else ramp[0]
    c_after = t["emphasis"] if spec.highlight or before.role or after.role else t["categorical"][0]
    labels_on = spec.labels != "none"
    vals = [v for s in (before, after) for v in s.values]
    lo, hi, hi_fixed = C.domain_bounds(spec, vals, zero=False)
    cat_w = min(box.w * 0.32, max(C.measure(spec, theme, c, "body", sc.tick) for c in cats))
    plot_w = box.w - (cat_w + sc.tick * 0.7 + 4)
    r = sc.point_px * 0.7
    if labels_on or spec.annotations:
        lw = max(C.measure(spec, theme, spec.value_format.format(v), "numeric", sc.label) for v in vals if v is not None) if labels_on else 0
        gutter = lw + r + sc.label * 0.6
        ann_w = max((C.measure(spec, theme, a.text, "annotation", sc.annotation) for a in spec.annotations), default=0)
        gutter_r = gutter + (ann_w + sc.annotation * 1.2 if ann_w else 0)
        span = hi - lo
        usable = max(1.0, plot_w - gutter - gutter_r)
        lo_e, hi_e = lo - span * gutter / usable, hi + span * gutter_r / usable
        if spec.value_axis.min is None:
            lo = lo_e
        if not hi_fixed:
            hi = hi_e
    wide, long_ = [], []
    for c, i in zip(cats, order):
        b, a = before.values[i], after.values[i]
        wide.append({"category": c, "before": b, "after": a})
        long_.append({"category": c, "series": before.name, "value": b, "label": spec.value_format.format(b), "up": (a or 0) >= (b or 0), "is_after": False})
        long_.append({"category": c, "series": after.name, "value": a, "label": spec.value_format.format(a), "up": (a or 0) >= (b or 0), "is_after": True})
    cat_enc = {"field": "category", "type": "nominal", "sort": None,
               "axis": C.cat_axis(spec, theme, sc, cats, max_label_w=box.w * 0.32, highlight=spec.highlight, baseline=False,
                                  title=spec.category_axis.label or None),
               "scale": {"paddingInner": 0.4, "paddingOuter": 0.2}}
    val_scale = {"domain": [lo, hi], "nice": False, "zero": False}
    val_axis = None if labels_on else C.value_axis(spec, theme, sc, title=spec.value_axis.label or None)
    layers = [
        {"data": {"values": wide}, "mark": {"type": "rule", "strokeWidth": 2, "color": t["deemphasis"], "strokeCap": "round"},
         "encoding": {"y": cat_enc, "x": {"field": "before", "type": "quantitative", "scale": val_scale, "axis": val_axis},
                      "x2": {"field": "after"}}},
        {"data": {"values": long_}, "mark": {"type": "point", "filled": True, "size": C.point_area(sc.point_px * 1.4), "stroke": t["surface"], "strokeWidth": 2},
         "encoding": {"y": cat_enc, "x": {"field": "value", "type": "quantitative", "scale": val_scale, "axis": val_axis},
                      "color": C.legend_for([before.name, after.name], {before.name: c_before, after.name: c_after})}},
    ]
    if labels_on:
        dx = round(r + sc.label * 0.45)
        layers.append({"data": {"values": long_},
                       "mark": {"type": "text", "baseline": "middle", **C.font(theme, sc, "numeric"),
                                "align": {"expr": "(datum.is_after == datum.up) ? 'left' : 'right'"},
                                "dx": {"expr": f"(datum.is_after == datum.up) ? {dx} : -{dx}"},
                                "fontWeight": {"expr": f"datum.is_after ? {theme.weight('numeric')} : 400"}},
                       "encoding": {"y": cat_enc, "x": {"field": "value", "type": "quantitative", "scale": val_scale, "axis": val_axis},
                                    "text": {"field": "label"},
                                    "color": {"condition": {"test": "datum.is_after", "value": t["ink"]}, "value": t["secondary"]}}})
    for a in spec.annotations:
        if a.target in cats:
            i = order[cats.index(a.target)]
            b, af = before.values[i] or 0, after.values[i] or 0
            outer = max(b, af)
            lw = C.measure(spec, theme, spec.value_format.format(outer), "numeric", sc.label) if labels_on else 0
            layers.append({"data": {"values": [{"category": a.target, "x": outer}]},
                           "mark": {"type": "text", "align": "left", "baseline": "middle", "dx": round(r + sc.label * 0.45 + lw + sc.annotation * 0.7),
                                    **C.font(theme, sc, "annotation", size=sc.annotation, color=t["secondary"])},
                           "encoding": {"y": cat_enc, "x": {"field": "x", "type": "quantitative", "scale": val_scale, "axis": val_axis},
                                        "text": {"value": a.text}}})
    return {"layer": layers}
