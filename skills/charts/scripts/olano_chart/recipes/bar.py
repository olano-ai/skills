"""bar — horizontal bars, the default form for comparing categories.

One series, one hue (slot 1).  ``highlight`` paints the named bars in the theme's
emphasis colour and the rest in the de-emphasis gray; ``ordinal: true`` uses the
one-hue ramp.  Values sit at the bar tip — outside when any bar is shorter than
about 2.5× its label — and the value axis disappears once every bar is labelled.
Copy this file to start a custom recipe (``--recipe my_bar.py``).
"""
from __future__ import annotations

from . import _common as C

SUPPORTS_ANNOTATIONS = True


def preferred_height(spec, sc, chart_w):
    n = len(spec.categories)
    axis = sc.tick * 2.4 if spec.labels == "none" else sc.tick * 0.6
    return n * sc.row_step_max + axis


def build(spec, theme) -> dict:
    sc, box, t = C.sc(spec), C.box(spec), theme.tokens
    order = spec.order()
    cats = [spec.categories[i] for i in order]
    vals = [spec.series[0].values[i] for i in order]
    n = len(cats)
    colors = C.category_colors(spec, theme, cats)
    labels_on = spec.labels != "none"
    texts = [spec.label_for(v) for v in vals]

    # --- geometry estimates (Vega measures for real; these decide label placement) ---
    max_cat_w = box.w * 0.32
    cat_w = min(max_cat_w, max(C.measure(spec, theme, c, "body", sc.tick) for c in cats))
    plot_w = box.w - (cat_w + sc.tick * 0.7 + 4)
    lo, hi, hi_fixed = C.domain_bounds(spec, vals)
    label_w = [C.measure(spec, theme, s, "numeric", sc.label) for s in texts]
    ann = {a.target: a for a in spec.annotations if a.target in cats}
    ann_w = {c: C.measure(spec, theme, a.text, "annotation", sc.annotation) for c, a in ann.items()}
    plot_h = box.h - (0 if labels_on else sc.tick * 2.2)
    bar_h = min(sc.bar_cap, (plot_h / n) * 0.72)
    bar_px = [((v or 0) - lo) / (hi - lo) * plot_w for v in vals]
    outside = (not labels_on) or bar_h < sc.label * 1.25 or any(
        bp < 2.5 * lw + sc.label * 0.5 for bp, lw in zip(bar_px, label_w))
    if not hi_fixed:
        if labels_on and outside:
            gutter = max(lw + sc.label * 0.5 + (ann_w[c] + sc.annotation * 0.9 if c in ann_w else 0)
                         for lw, c in zip(label_w, cats))
        else:
            gutter = (max(ann_w.values()) + sc.annotation) if ann_w else 0
        if gutter:
            hi = C.extend_domain(lo, hi, plot_w, gutter + sc.label * 0.3)

    rows = []
    for i, c in enumerate(cats):
        strong = (not spec.highlight) or (c in spec.highlight)
        rows.append({"category": c, "value": vals[i], "label": texts[i], "color": colors[i],
                     "lbl": t["ink"] if strong else t["secondary"], "lblw": 700 if strong else 400,
                     "inside": C.inside_ink(theme, colors[i])})

    y = {"field": "category", "type": "nominal", "sort": None,
         "axis": C.cat_axis(spec, theme, sc, cats, max_label_w=max_cat_w, highlight=spec.highlight,
                            title=spec.category_axis.label or None),
         "scale": {"paddingInner": 0.3, "paddingOuter": 0.12}}
    x = {"field": "value", "type": "quantitative", "scale": {"domain": [lo, hi], "nice": False, "zero": False},
         "axis": None if labels_on else C.value_axis(spec, theme, sc, title=spec.value_axis.label or None)}
    layers = [{"mark": {"type": "bar", "height": round(bar_h, 1), "cornerRadiusEnd": 4},
               "encoding": {"y": y, "x": x, "color": {"field": "color", "type": "nominal", "scale": None, "legend": None}}}]
    if labels_on:
        if outside:
            mark = {"type": "text", "align": "left", "baseline": "middle", "dx": round(sc.label * 0.45), **C.font(theme, sc, "numeric")}
            color = {"field": "lbl", "type": "nominal", "scale": None, "legend": None}
        else:
            mark = {"type": "text", "align": "right", "baseline": "middle", "dx": -round(sc.label * 0.5), **C.font(theme, sc, "numeric")}
            color = {"field": "inside", "type": "nominal", "scale": None, "legend": None}
        mark["fontWeight"] = {"expr": "datum.lblw"}
        layers.append({"mark": mark, "encoding": {"y": y, "x": x, "text": {"field": "label"}, "color": color}})
    for c, a in ann.items():
        i = cats.index(c)
        dx = (label_w[i] + sc.label * 0.45 + sc.annotation * 0.7) if (labels_on and outside) else sc.annotation * 0.5
        layers.append({"mark": {"type": "text", "align": "left", "baseline": "middle", "dx": round(dx),
                                **C.font(theme, sc, "annotation", size=sc.annotation, color=t["secondary"])},
                       "transform": [C.filter_eq("category", c)],
                       "encoding": {"y": y, "x": x, "text": {"value": a.text}}})
    return {"data": {"values": rows}, "layer": layers}
