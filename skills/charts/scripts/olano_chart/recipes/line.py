"""line — a trend over an ordered sequence, one line per series.

2px lines with round joins, ≥ 8px points with a 2px surface ring, a legend for
two or more series and selective direct labels: ``auto`` labels the line ends
(name · value) and drops to legend-only when two end values would collide;
``extremes`` labels each series' high and low; ``ends`` labels first and last.
"""
from __future__ import annotations

from . import _common as C

SUPPORTS_ANNOTATIONS = True


def preferred_height(spec, sc, chart_w):
    return chart_w * 0.6


def build(spec, theme) -> dict:
    return build_lines(spec, theme)


def build_lines(spec, theme, area: bool = False) -> dict:
    sc, box, t = C.sc(spec), C.box(spec), theme.tokens
    cats = list(spec.categories)
    n = len(cats)
    names = [s.name for s in spec.series]
    colors = C.series_colors(spec, theme)
    multi = len(names) > 1
    focus = spec.emphasis_series()[0] if spec.emphasis_series() else (spec.highlight[0] if spec.highlight and spec.highlight[0] in names else names[0])
    all_vals = [v for s in spec.series for v in s.values]
    lo, hi, hi_fixed = C.domain_bounds(spec, all_vals, zero=not area or spec.value_axis.min is None)
    legend_h = sc.legend * 2.6 if multi else 0
    plot_h = box.h - legend_h - sc.tick * 2.6
    plot_w = box.w - sc.tick * 3.4

    # --- which labels ---------------------------------------------------------
    mode = spec.labels
    want_ends = mode in ("auto", "ends")
    want_all = mode == "all" and n <= 12
    want_extremes = mode == "extremes" or (mode == "all" and n > 12)
    end_texts = {}
    for s in spec.series:
        v = s.values[-1]
        end_texts[s.name] = (f"{s.name} · {spec.value_format.format(v)}" if multi else spec.value_format.format(v))
    if want_ends and multi:
        ys = sorted(((s.values[-1] or lo) - lo) / (hi - lo) * plot_h for s in spec.series)
        if any(b - a < sc.label * 1.15 for a, b in zip(ys, ys[1:])):
            want_ends = False  # converging ends: the legend carries identity
    right_pad = 0
    if want_ends:
        right_pad = max(C.measure(spec, theme, s, "numeric", sc.label) for s in end_texts.values()) + sc.point_px + sc.label * 0.6

    rows = []
    for s in spec.series:
        known = [v for v in s.values if v is not None]
        vmax, vmin = (max(known), min(known)) if known else (None, None)
        for i, c in enumerate(cats):
            v = s.values[i]
            is_end = i == n - 1
            is_start = i == 0
            show = v is not None and (want_all or (want_ends and is_end) or (mode == "ends" and is_start)
                                      or (want_extremes and v in (vmax, vmin)))
            prev_v = s.values[i - 1] if i > 0 else None
            next_v = s.values[i + 1] if i < n - 1 else None
            below = v is not None and (prev_v is None or prev_v >= v) and (next_v is None or next_v >= v) and not (prev_v is None and next_v is None)
            rows.append({"category": c, "i": i, "series": s.name, "value": v,
                         "label": end_texts[s.name] if (is_end and want_ends and not want_all) else spec.value_format.format(v),
                         "show": show, "is_end": is_end, "focus": s.name == focus, "below": below,
                         "color": colors[s.name]})

    widest = max(C.measure(spec, theme, c, "body", sc.tick) for c in cats)
    step_px = (plot_w - right_pad) / max(1, n - 1)
    every = max(1, -(-int(1.45 * widest) // max(1, int(step_px))))  # ceil(1.45 * widest / step)
    x_axis = {"title": spec.category_axis.label or None, "labelColor": t["muted"], "domain": True,
              "domainColor": t["baseline"], "grid": False, "ticks": False, "labelAngle": 0,
              "labelOverlap": "parity", "labelFlush": True, "labelPadding": round(sc.tick * 0.7)}
    if every > 1:
        x_axis["values"] = [cats[i] for i in range(n - 1, -1, -every)][::-1]  # keep the last point, thin backwards
    x = {"field": "category", "type": "ordinal", "sort": None,
         "scale": {"type": "point", "padding": 0.12},
         "axis": x_axis}
    y_scale = {"domain": [lo, hi], "nice": not (spec.value_axis.min is not None or spec.value_axis.max is not None)}
    if not hi_fixed and spec.value_axis.min is None:
        y_scale = {"zero": True, "nice": True} if not area else {"zero": True, "nice": True}
    y = {"field": "value", "type": "quantitative", "scale": y_scale,
         "axis": C.value_axis(spec, theme, sc, title=spec.value_axis.label or None)}
    color = C.legend_for(names, colors)
    if not multi:
        color = {**color, "legend": None}

    layers = []
    if area:
        layers.append({"mark": {"type": "area", "line": False, "opacity": 0.12, "interpolate": "monotone" if n > 24 else "linear"},
                       "encoding": {"x": x, "y": y, "color": {**color, "legend": None}}})
    layers.append({"mark": {"type": "line", "strokeWidth": 2, "strokeJoin": "round", "strokeCap": "round",
                            "interpolate": "monotone" if n > 24 else "linear"},
                   "encoding": {"x": x, "y": y, "color": color, "detail": {"field": "series"}}})
    pts = {"type": "point", "filled": True, "size": C.point_area(sc.point_px), "stroke": t["surface"], "strokeWidth": 2}
    point_filter = [] if n <= 30 else [{"filter": "datum.is_end || datum.i == 0"}]
    layers.append({"mark": pts, "transform": point_filter + [{"filter": "isValid(datum.value)"}],
                   "encoding": {"x": x, "y": y, "color": {**color, "legend": None}}})
    if want_ends or want_all or want_extremes:
        if want_ends and not want_all and not want_extremes:
            mark = {"type": "text", "align": "left", "baseline": "middle", "dx": round(sc.point_px / 2 + sc.label * 0.4)}
        else:
            off = round(sc.point_px / 2 + sc.label * 0.35)
            mark = {"type": "text", "align": {"expr": "datum.i == 0 ? 'left' : (datum.is_end ? 'right' : 'center')"},
                    "baseline": {"expr": "datum.below ? 'top' : 'bottom'"}, "dy": {"expr": f"datum.below ? {off} : -{off}"}}
        layers.append({"mark": {**mark, **C.font(theme, sc, "numeric")}, "transform": [{"filter": "datum.show"}],
                       "encoding": {"x": x, "y": y, "text": {"field": "label"},
                                    "color": {"value": t["ink"]}, "detail": {"field": "series"}}})
    focus_vals = next(s.values for s in spec.series if s.name == focus)
    for a in spec.annotations:
        if a.target in cats:
            i = cats.index(a.target)
            filt = [C.filter_eq("category", a.target), C.filter_eq("series", focus)]
            vals_here = focus_vals
        elif a.target in names:
            i = n - 1
            filt = [C.filter_eq("series", a.target), {"filter": "datum.is_end"}]
            vals_here = next(s.values for s in spec.series if s.name == a.target)
        else:
            continue
        # Sit the note on the side where the line is lower, so a rising line never runs through it.
        prev_v = vals_here[i - 1] if i > 0 and vals_here[i - 1] is not None else None
        next_v = vals_here[i + 1] if i < n - 1 and vals_here[i + 1] is not None else None
        cur = vals_here[i] if vals_here[i] is not None else 0
        rising = (next_v is not None and next_v > cur) or (next_v is None and prev_v is not None and prev_v < cur)
        if i == n - 1:
            align, dx = "right", -round(sc.point_px * 0.6)
        elif i == 0:
            align, dx = "left", round(sc.point_px * 0.6)
        elif rising:
            align, dx = "right", -round(sc.point_px * 0.6)
        else:
            align, dx = "left", round(sc.point_px * 0.6)
        layers.append({"mark": {"type": "text", "align": align, "baseline": "bottom", "dx": dx,
                                "dy": -round(sc.point_px / 2 + sc.annotation * 0.55),
                                **C.font(theme, sc, "annotation", size=sc.annotation, color=t["secondary"])},
                       "transform": filt, "encoding": {"x": x, "y": y, "text": {"value": a.text}}})
    # No explicit right/top padding: autosize "fit" measures the end labels and annotations
    # that overflow the plot and makes room for them (an explicit pad would double it).
    return {"data": {"values": rows}, "layer": layers}
