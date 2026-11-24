"""scatter — two measures per point.  Filled points ≥ 8px with a 2px surface ring;
up to three groups (any two dots can touch, so only three hues stay distinct);
``highlight`` names points by label; labels are selective (all when ≤ 20 points,
otherwise the four extremes).
"""
from __future__ import annotations

from . import _common as C

SUPPORTS_ANNOTATIONS = True


def preferred_height(spec, sc, chart_w):
    return chart_w * 0.7


def build(spec, theme) -> dict:
    sc, box, t = C.sc(spec), C.box(spec), theme.tokens
    pts = spec.points
    groups = sorted({p.group for p in pts if p.group})
    gcolors = dict(zip(groups, theme.series_colors(len(groups)))) if groups else {}
    n = len(pts)
    xs, ys = [p.x for p in pts], [p.y for p in pts]
    extremes = {max(pts, key=lambda p: p.x).label, min(pts, key=lambda p: p.x).label,
                max(pts, key=lambda p: p.y).label, min(pts, key=lambda p: p.y).label}
    label_all = spec.labels == "all" or (spec.labels == "auto" and n <= 20)
    rows = []
    for p in pts:
        hl = bool(spec.highlight) and (p.label in spec.highlight or p.group in spec.highlight)
        if spec.highlight:
            col = t["emphasis"] if hl else t["deemphasis"]
        else:
            col = gcolors.get(p.group, t["categorical"][0])
        show = bool(p.label) and spec.labels != "none" and (label_all or p.label in extremes or hl or spec.labels == "ends" and p.label in extremes)
        rows.append({"x": p.x, "y": p.y, "label": p.label, "group": p.group or "", "color": col, "show": show,
                     "lbl": t["ink"] if (not spec.highlight or hl) else t["secondary"]})
    x = {"field": "x", "type": "quantitative", "scale": {"zero": False, "nice": True},
         "axis": {"title": spec.x_axis.label or None, "grid": True, "domain": False, "ticks": False, "labelFlush": True,
                  "labelExpr": "format(datum.value, ',.2~f')", "tickCount": 6}}
    y = {"field": "y", "type": "quantitative", "scale": {"zero": False, "nice": True},
         "axis": C.value_axis(spec, theme, sc, title=spec.value_axis.label or None, tick_count=6)}
    if groups and not spec.highlight:
        color = {"field": "group", "type": "nominal", "sort": None, "scale": {"domain": groups, "range": [gcolors[g] for g in groups]},
                 "legend": {"values": groups}}
    else:
        color = {"field": "color", "type": "nominal", "scale": None, "legend": None}
    size = C.point_area(sc.point_px * 1.5)
    layers = [{"mark": {"type": "point", "filled": True, "size": size, "stroke": t["surface"], "strokeWidth": 2, "opacity": 1},
               "encoding": {"x": x, "y": y, "color": color}}]
    layers.append({"mark": {"type": "text", "align": "left", "baseline": "middle", "dx": round(sc.point_px * 0.75 + sc.label * 0.35),
                            **C.font(theme, sc, "body", size=sc.tick, weight=400)},
                   "transform": [{"filter": "datum.show"}],
                   "encoding": {"x": x, "y": y, "text": {"field": "label"}, "color": {"field": "lbl", "type": "nominal", "scale": None, "legend": None}}})
    for a in spec.annotations:
        layers.append({"mark": {"type": "text", "align": "left", "baseline": "bottom", "dx": round(sc.point_px * 0.75 + sc.label * 0.35), "dy": -round(sc.tick * 0.9),
                                **C.font(theme, sc, "annotation", size=sc.annotation, color=t["secondary"])},
                       "transform": [C.filter_eq("label", a.target)] if a.target not in groups else [C.filter_eq("group", a.target), {"filter": "datum.show"}],
                       "encoding": {"x": x, "y": y, "text": {"value": a.text}}})
    # autosize "fit" absorbs overflowing labels, but a mark anchored near (not at) the right edge
    # keeps a small residual after Vega's passes — cover it with a fraction of the widest overflow.
    widest = max([C.measure(spec, theme, r["label"], "body", sc.tick) for r in rows if r["show"]] +
                 [C.measure(spec, theme, a.text, "annotation", sc.annotation) for a in spec.annotations] + [0])
    return {"data": {"values": rows}, "layer": layers, "padding": {"right": round(0.15 * widest + 4)}}
