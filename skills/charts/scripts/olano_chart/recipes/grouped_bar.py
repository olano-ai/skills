"""grouped_bar — several series side by side per category (horizontal by default).

Bars inside a group are separated by a 2px surface gap and never exceed the
thickness cap; every bar is labelled while the chart has ≤ 16 bars, after which
the value axis carries the numbers.  The legend is always present.
"""
from __future__ import annotations

from . import _common as C

SUPPORTS_ANNOTATIONS = True


def preferred_height(spec, sc, chart_w):
    if spec.orientation == "vertical":
        return chart_w * 0.62
    k = len(spec.series)
    return len(spec.categories) * (k * (sc.bar_cap + 2) + sc.bar_cap * 1.3) + sc.legend * 2.6 + sc.tick * 2.4


def build(spec, theme) -> dict:
    sc, box, t = C.sc(spec), C.box(spec), theme.tokens
    horizontal = spec.orientation != "vertical"
    order = spec.order()
    cats = [spec.categories[i] for i in order]
    names = [s.name for s in spec.series]
    k = len(names)
    colors = C.series_colors(spec, theme)
    all_vals = [v for s in spec.series for v in s.values]
    n_bars = len(cats) * k
    labels_on = spec.labels == "all" or (spec.labels in ("auto", "ends", "extremes") and n_bars <= 16)
    lo, hi, hi_fixed = C.domain_bounds(spec, all_vals)
    texts = {(c, s.name): spec.value_format.format(s.values[i]) for c, i in zip(cats, order) for s in spec.series}

    if horizontal:
        cat_w = min(box.w * 0.32, max(C.measure(spec, theme, c, "body", sc.tick) for c in cats))
        plot_len = box.w - (cat_w + sc.tick * 0.7 + 4)
        plot_h = box.h - sc.legend * 2.6 - (0 if labels_on else sc.tick * 2.4)
        group = plot_h / len(cats) * 0.7
        thick = min(sc.bar_cap, group / k - 2)
        gutter = (max(C.measure(spec, theme, s, "numeric", sc.label) for s in texts.values()) + sc.label * 0.7) if labels_on else 0
    else:
        plot_len = box.h - sc.legend * 2.6 - sc.tick * 2.6
        group = (box.w - (0 if labels_on else sc.tick * 3.2)) / len(cats) * 0.7
        thick = min(sc.bar_cap * 1.3, group / k - 2)
        gutter = sc.label * 1.4 if labels_on else 0
    thick = max(4.0, thick)
    if spec.annotations and horizontal:
        ann_w = max(C.measure(spec, theme, a.text, "annotation", sc.annotation) for a in spec.annotations)
        gutter += ann_w + sc.annotation * 1.2
    elif spec.annotations:
        gutter += sc.annotation * 1.6
    if not hi_fixed and gutter:
        hi = C.extend_domain(lo, hi, plot_len, gutter)

    rows = [{"category": c, "series": s.name, "value": s.values[i], "label": texts[(c, s.name)],
             "lbl": t["ink"] if (not spec.emphasis_series() and not spec.highlight) or s.name in spec.emphasis_series() or s.name in spec.highlight else t["secondary"]}
            for c, i in zip(cats, order) for s in spec.series]
    cat_enc = {"field": "category", "type": "nominal", "sort": None,
               "axis": C.cat_axis(spec, theme, sc, cats, max_label_w=(box.w * 0.32 if horizontal else box.w / len(cats) * 0.92),
                                  highlight=spec.highlight, title=spec.category_axis.label or None),
               "scale": {"paddingInner": 0.3, "paddingOuter": 0.12}}
    off = {"field": "series", "type": "nominal", "sort": None, "scale": {"paddingInner": 0, "paddingOuter": 0}}
    val = {"field": "value", "type": "quantitative", "scale": {"domain": [lo, hi], "nice": False, "zero": False},
           "axis": None if labels_on else C.value_axis(spec, theme, sc, title=spec.value_axis.label or None)}
    if horizontal:
        pos = {"y": cat_enc, "yOffset": off, "x": val}
        mark = {"type": "bar", "height": round(thick, 1), "cornerRadiusEnd": 4}
        lab = {"type": "text", "align": "left", "baseline": "middle", "dx": round(sc.label * 0.45)}
    else:
        pos = {"x": cat_enc, "xOffset": off, "y": val}
        mark = {"type": "bar", "width": round(thick, 1), "cornerRadiusEnd": 4}
        lab = {"type": "text", "align": "center", "baseline": "bottom", "dy": -round(sc.label * 0.4)}
    layers = [{"mark": mark, "encoding": {**pos, "color": C.legend_for(names, colors)}}]
    if labels_on:
        layers.append({"mark": {**lab, **C.font(theme, sc, "numeric", size=round(sc.label * (0.9 if k >= 3 else 1.0)))},
                       "encoding": {**pos, "text": {"field": "label"},
                                    "color": {"field": "lbl", "type": "nominal", "scale": None, "legend": None}}})
    for a in spec.annotations:
        if a.target in cats:
            i = order[cats.index(a.target)]
            best = max(spec.series, key=lambda s: (s.values[i] or 0))
            tw = C.measure(spec, theme, texts[(a.target, best.name)], "numeric", sc.label) if labels_on else 0
            if horizontal:
                m = {"type": "text", "align": "left", "baseline": "middle", "dx": round(tw + sc.label * 0.5 + sc.annotation * 0.7)}
            else:
                m = {"type": "text", "align": "center", "baseline": "bottom", "dy": -round((sc.label * 1.75 if labels_on else sc.label * 0.4) + sc.annotation * 0.4)}
            layers.append({"mark": {**m, **C.font(theme, sc, "annotation", size=sc.annotation, color=t["secondary"])},
                           "transform": [C.filter_eq("category", a.target), C.filter_eq("series", best.name)],
                           "encoding": {**pos, "text": {"value": a.text}}})
        elif a.target in names:
            i_best = max(range(len(cats)), key=lambda j: (next(s for s in spec.series if s.name == a.target).values[order[j]] or 0))
            c = cats[i_best]
            tw = C.measure(spec, theme, texts[(c, a.target)], "numeric", sc.label) if labels_on else 0
            m = ({"type": "text", "align": "left", "baseline": "middle", "dx": round(tw + sc.label * 0.5 + sc.annotation * 0.7)} if horizontal
                 else {"type": "text", "align": "center", "baseline": "bottom", "dy": -round((sc.label * 1.75 if labels_on else sc.label * 0.4) + sc.annotation * 0.4)})
            layers.append({"mark": {**m, **C.font(theme, sc, "annotation", size=sc.annotation, color=t["secondary"])},
                           "transform": [C.filter_eq("category", c), C.filter_eq("series", a.target)],
                           "encoding": {**pos, "text": {"value": a.text}}})
    return {"data": {"values": rows}, "layer": layers}
