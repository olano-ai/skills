"""stacked_bar — part-to-whole per category, several series stacked (horizontal by default).

Stacking is done here in Python (start/end per segment) so labels know whether
they fit.  Segments are separated by a 2px surface gap, only the outer segment
gets the rounded end, totals sit at the bar tip, and a legend is always present.
``orientation: "vertical"`` turns the stack into columns.
"""
from __future__ import annotations

from . import _common as C

SUPPORTS_ANNOTATIONS = True


def preferred_height(spec, sc, chart_w):
    if spec.orientation == "vertical":
        return chart_w * 0.62
    n = len(spec.categories)
    return n * sc.row_step_max + sc.legend * 2.6 + sc.tick * 2.4


def build(spec, theme) -> dict:
    sc, box, t = C.sc(spec), C.box(spec), theme.tokens
    horizontal = spec.orientation != "vertical"
    order = spec.order()
    cats = [spec.categories[i] for i in order]
    names = [s.name for s in spec.series]
    colors = C.series_colors(spec, theme)
    show_totals = spec.labels in ("auto", "ends", "all", "extremes")
    show_segments = spec.labels in ("auto", "all")

    totals = {c: sum((s.values[i] or 0) for s in spec.series) for c, i in zip(cats, order)}
    lo, hi, hi_fixed = C.domain_bounds(spec, list(totals.values()))
    total_txt = {c: spec.value_format.format(totals[c]) for c in cats}
    if horizontal:
        cat_w = min(box.w * 0.32, max(C.measure(spec, theme, c, "body", sc.tick) for c in cats))
        plot_len = box.w - (cat_w + sc.tick * 0.7 + 4)
        gutter = max(C.measure(spec, theme, s, "numeric", sc.label) for s in total_txt.values()) + sc.label * 0.7 if show_totals else 0
        band = (box.h - sc.legend * 2.6 - sc.tick * 2.4) / len(cats)
        thick = min(sc.bar_cap, band * 0.72)
    else:
        plot_len = box.h - sc.legend * 2.6 - sc.tick * 2.6
        gutter = sc.label * 1.4 if show_totals else 0
        band = box.w / len(cats)
        thick = min(sc.bar_cap * 1.5, band * 0.62)
    if not hi_fixed and gutter:
        hi = C.extend_domain(lo, hi, plot_len, gutter)
    px_per_unit = plot_len / (hi - lo)

    rows = []
    for c, i in zip(cats, order):
        start = 0.0
        segs = [(s.name, s.values[i] or 0) for s in spec.series]
        last_idx = max((k for k, (_, v) in enumerate(segs) if v > 0), default=len(segs) - 1)
        for k, (name, v) in enumerate(segs):
            end = start + v
            label = spec.value_format.format(v)
            lw = C.measure(spec, theme, label, "numeric", sc.label)
            seg_px = v * px_per_unit
            fits = show_segments and v > 0 and (seg_px >= lw + sc.label * 0.9 if horizontal else (seg_px >= sc.label * 1.5 and thick >= lw + sc.label * 0.6))
            rows.append({"category": c, "series": name, "start": start, "end": end, "mid": (start + end) / 2,
                         "value": v, "label": label, "fits": fits, "is_last": k == last_idx,
                         "inside": C.inside_ink(theme, colors[name]), "total": totals[c], "total_label": total_txt[c]})
            start = end

    cat_enc = {"field": "category", "type": "nominal", "sort": None,
               "axis": C.cat_axis(spec, theme, sc, cats, max_label_w=(box.w * 0.32 if horizontal else band * 0.92),
                                  highlight=spec.highlight, title=spec.category_axis.label or None),
               "scale": {"paddingInner": 0.3, "paddingOuter": 0.12}}
    val_scale = {"domain": [lo, hi], "nice": False, "zero": False}
    val_axis = C.value_axis(spec, theme, sc, title=spec.value_axis.label or None)
    if horizontal:
        pos = {"y": cat_enc, "x": {"field": "start", "type": "quantitative", "scale": val_scale, "axis": val_axis},
               "x2": {"field": "end"}}
        size_key = "height"
    else:
        pos = {"x": cat_enc, "y": {"field": "start", "type": "quantitative", "scale": val_scale, "axis": val_axis},
               "y2": {"field": "end"}}
        size_key = "width"
    bar = {"mark": {"type": "bar", size_key: round(thick, 1), "stroke": t["surface"], "strokeWidth": 2,
                    "cornerRadiusEnd": {"expr": "datum.is_last ? 4 : 0"}},
           "encoding": {**pos, "color": C.legend_for(names, colors)}}
    layers = [bar]
    if show_segments:
        mid = {"field": "mid", "type": "quantitative", "scale": val_scale}
        enc = {"y": cat_enc, "x": mid} if horizontal else {"x": cat_enc, "y": mid}
        layers.append({"mark": {"type": "text", "align": "center", "baseline": "middle", **C.font(theme, sc, "numeric", weight=theme.weight("numeric"))},
                       "transform": [{"filter": "datum.fits"}],
                       "encoding": {**enc, "text": {"field": "label"},
                                    "color": {"field": "inside", "type": "nominal", "scale": None, "legend": None}}})
    if show_totals:
        tot = {"field": "total", "type": "quantitative", "scale": val_scale}
        if horizontal:
            mark = {"type": "text", "align": "left", "baseline": "middle", "dx": round(sc.label * 0.5)}
            enc = {"y": cat_enc, "x": tot}
        else:
            mark = {"type": "text", "align": "center", "baseline": "bottom", "dy": -round(sc.label * 0.4)}
            enc = {"x": cat_enc, "y": tot}
        layers.append({"mark": {**mark, **C.font(theme, sc, "numeric")}, "transform": [{"filter": "datum.is_last"}],
                       "encoding": {**enc, "text": {"field": "total_label"}}})
    for a in spec.annotations:
        if a.target in cats:
            tot = {"field": "total", "type": "quantitative", "scale": val_scale}
            tw = C.measure(spec, theme, total_txt[a.target], "numeric", sc.label) if show_totals else 0
            if horizontal:
                mark = {"type": "text", "align": "left", "baseline": "middle", "dx": round(tw + sc.label * 0.5 + sc.annotation * 0.7)}
                enc = {"y": cat_enc, "x": tot}
            else:
                mark = {"type": "text", "align": "center", "baseline": "bottom", "dy": -round(sc.label * 1.75 + sc.annotation * 0.4)}
                enc = {"x": cat_enc, "y": tot}
            layers.append({"mark": {**mark, **C.font(theme, sc, "annotation", size=sc.annotation, color=t["secondary"])},
                           "transform": [C.filter_eq("category", a.target), {"filter": "datum.is_last"}],
                           "encoding": {**enc, "text": {"value": a.text}}})
    return {"data": {"values": rows}, "layer": layers}
