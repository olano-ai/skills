"""The HTML page: chrome, inlined fonts, the vendored Vega scripts, ``vegaEmbed`` and
the ``.render-done`` sentinel — plus the optional native SVG card (``--svg-card``).

The chrome is positioned from the numbers ``layout.py`` computed, each line as its
own non-wrapping span, so the page and the SVG card place every glyph at the same
coordinates.  Vega gets ``#chart`` and fits itself inside it (``autosize: fit``).
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

from .fonts import font_face_css
from .themes import deep_merge

SCHEMA = "https://vega.github.io/schema/vega-lite/v6.json"
VENDOR_DIR = Path(__file__).resolve().parents[2] / "assets" / "vendor"
VENDOR_FILES = ("vega.min.js", "vega-lite.min.js", "vega-embed.min.js")


def vendor_uris() -> list[str]:
    uris = []
    for name in VENDOR_FILES:
        p = VENDOR_DIR / name
        if not p.is_file():
            raise ValueError(f"vendored script missing: {p} — the skill's assets/vendor directory is incomplete")
        uris.append(p.as_uri())
    return uris


def finalize_vl(vl: dict, theme, layout, *, force_size: bool = True) -> dict:
    """Add schema, theme config and the chart box size to a recipe's Vega-Lite spec."""
    out = dict(vl)
    out.setdefault("$schema", SCHEMA)
    out["config"] = deep_merge(theme.vega_config(layout.scale), out.get("config") or {})
    box = layout.chart
    if box is not None:
        single_or_layer = "mark" in out or "layer" in out
        if force_size or ("width" not in out and "height" not in out):
            if single_or_layer:
                out["width"] = round(box.w)
                out["height"] = round(box.h)
                out["autosize"] = {"type": "fit", "contains": "padding"}
                pad = out.get("padding")
                base_pad = {"left": 4, "right": 4, "top": 2, "bottom": 2}
                if isinstance(pad, dict):
                    out["padding"] = {**base_pad, **pad}
                elif isinstance(pad, (int, float)):
                    out["padding"] = {k: max(v, pad) for k, v in base_pad.items()}
                else:
                    out["padding"] = base_pad
    return out


def _js(obj) -> str:
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def build_page(layout, theme, vl: dict | None = None, *, body_markup: str | None = None, body_fit: dict | None = None,
               svg_card: bool = False, embed_fonts: bool = False, page_title: str = "Chart", meta: dict | None = None) -> str:
    t = theme.tokens
    faces = theme.fontset.available_faces() if theme.fontset else []
    face_css = font_face_css(faces)
    W, H = layout.width, layout.height
    blocks_html = []
    for b in layout.blocks:
        style = (f"left:{b.x:.2f}px;top:{b.y:.2f}px;width:{b.w:.2f}px;font-family:{b.stack};font-size:{b.size}px;"
                 f"line-height:{b.line_height}px;font-weight:{b.weight};font-style:{b.style};color:{b.color};")
        if b.letter_spacing_em:
            style += f"letter-spacing:{b.letter_spacing_em}em;"
        cls = f"blk {b.role}" + (" right" if b.align == "right" else "")
        lines = "".join(f'<span class="ln">{html.escape(ln) or "&nbsp;"}</span>' for ln in b.lines)
        # The font stack carries double quotes; escape so the style attribute survives intact.
        blocks_html.append(f'<div class="{cls}" style="{html.escape(style, quote=True)}">{lines}</div>')
    for r in layout.rules:
        blocks_html.append(f'<div class="rule" style="left:{r.x1:.2f}px;top:{r.y1:.2f}px;width:{(r.x2 - r.x1):.2f}px;border-top:{r.width}px solid {r.color};"></div>')
    if layout.logo:
        lb = layout.logo.box
        blocks_html.append(f'<img id="logo" alt="" src="{layout.logo.data_uri}" style="left:{lb.x:.2f}px;top:{lb.y:.2f}px;width:{lb.w:.2f}px;height:{lb.h:.2f}px;">')
    chart_html = ""
    if layout.chart is not None:
        cb = layout.chart
        inner = body_markup or ""
        chart_html = f'<div id="chart" style="left:{cb.x:.2f}px;top:{cb.y:.2f}px;width:{cb.w:.2f}px;height:{cb.h:.2f}px;">{inner}</div>'

    has_vega = vl is not None
    scripts = "".join(f'<script src="{u}"></script>' for u in vendor_uris()) if has_vega else ""
    cfg = {
        "hasVega": has_vega,
        "spec": vl,
        "fontLoads": theme.fontset.load_descriptors() if theme.fontset else [],
        "svgCard": bool(svg_card),
        "embedCss": face_css if (svg_card and embed_fonts) else "",
        "bodyFit": body_fit,
        "layout": {**layout.as_dict(), "surface": t["surface"]},
        "meta": meta or {},
    }
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width={W}">
<title>{html.escape(page_title)}</title>
<style>
{face_css}
:root {{
  {theme.css_tokens()}
}}
html, body {{ margin: 0; padding: 0; background: var(--surface); }}
body {{ width: {W}px; height: {H}px; overflow: hidden; }}
#frame {{ position: relative; width: {W}px; height: {H}px; background: var(--surface); color: var(--ink);
  font-family: var(--font-body); overflow: hidden; -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility; }}
.blk {{ position: absolute; margin: 0; white-space: nowrap; }}
.blk .ln {{ display: block; }}
.blk.right {{ text-align: right; }}
.kicker {{ text-transform: uppercase; }}
.rule {{ position: absolute; height: 0; }}
#logo {{ position: absolute; object-fit: contain; }}
#chart {{ position: absolute; overflow: hidden; }}
#chart .vega-embed {{ display: block; width: 100%; height: 100%; }}
#chart .vega-embed summary, #chart .vega-embed details {{ display: none; }}
#chart > svg, #chart .vega-embed > svg {{ display: block; }}
#chart > svg {{ width: 100%; height: 100%; }}
.render-error {{ margin: 0; padding: 12px; font: 14px/1.4 ui-monospace, Menlo, monospace; color: var(--negative); white-space: pre-wrap; }}
#svg-card-holder {{ position: absolute; left: 0; top: 0; width: 0; height: 0; overflow: hidden; }}
</style>
</head>
<body>
<div id="frame" data-theme="{html.escape(theme.name)}" data-mode="{theme.mode}" data-preset="{html.escape(layout.preset)}">
{chr(10).join(blocks_html)}
{chart_html}
</div>
{scripts}
<script>
(function () {{
  var CFG = {_js(cfg)};
  function done(err) {{
    var d = document.createElement('div');
    d.className = 'render-done' + (err ? ' render-failed' : '');
    d.hidden = true;
    if (err) d.setAttribute('data-error', String(err && err.message || err));
    document.body.appendChild(d);
  }}
  function loadFonts() {{
    try {{
      var loads = CFG.fontLoads.map(function (f) {{ return document.fonts.load(f); }});
      return Promise.all(loads).then(function () {{ return document.fonts.ready; }}).catch(function () {{}});
    }} catch (e) {{ return Promise.resolve(); }}
  }}
  function svgCard(vegaSvg) {{
    var NS = 'http://www.w3.org/2000/svg', L = CFG.layout;
    var svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('xmlns', NS);
    svg.setAttribute('id', 'card');
    svg.setAttribute('width', L.width);
    svg.setAttribute('height', L.height);
    svg.setAttribute('viewBox', '0 0 ' + L.width + ' ' + L.height);
    if (CFG.embedCss) {{
      var st = document.createElementNS(NS, 'style');
      st.textContent = CFG.embedCss;
      svg.appendChild(st);
    }}
    var bg = document.createElementNS(NS, 'rect');
    bg.setAttribute('width', L.width); bg.setAttribute('height', L.height); bg.setAttribute('fill', L.surface);
    svg.appendChild(bg);
    L.rules.forEach(function (r) {{
      var ln = document.createElementNS(NS, 'line');
      ln.setAttribute('x1', r.x1); ln.setAttribute('y1', r.y1); ln.setAttribute('x2', r.x2); ln.setAttribute('y2', r.y2);
      ln.setAttribute('stroke', r.color); ln.setAttribute('stroke-width', r.width);
      svg.appendChild(ln);
    }});
    L.blocks.forEach(function (b) {{
      b.lines.forEach(function (line, i) {{
        var tx = document.createElementNS(NS, 'text');
        tx.setAttribute('x', b.align === 'right' ? (b.x + b.w) : b.x);
        tx.setAttribute('y', b.baselines[i]);
        tx.setAttribute('font-family', b.stack);
        tx.setAttribute('font-size', b.size);
        tx.setAttribute('font-weight', b.weight);
        if (b.style && b.style !== 'normal') tx.setAttribute('font-style', b.style);
        if (b.letterSpacing) tx.setAttribute('letter-spacing', (b.letterSpacing * b.size).toFixed(2));
        if (b.align === 'right') tx.setAttribute('text-anchor', 'end');
        tx.setAttribute('fill', b.color);
        tx.textContent = b.uppercase ? line.toUpperCase() : line;
        svg.appendChild(tx);
      }});
    }});
    if (L.logo) {{
      var im = document.createElementNS(NS, 'image');
      im.setAttribute('href', L.logo.href);
      im.setAttribute('x', L.logo.x); im.setAttribute('y', L.logo.y);
      im.setAttribute('width', L.logo.w); im.setAttribute('height', L.logo.h);
      im.setAttribute('preserveAspectRatio', 'xMidYMid meet');
      svg.appendChild(im);
    }}
    if (L.chart) {{
      var g = document.createElementNS(NS, 'g');
      var tr = 'translate(' + L.chart.x + ',' + L.chart.y + ')';
      var src = vegaSvg || document.querySelector('#chart > svg');
      if (!vegaSvg && src && CFG.bodyFit) tr += ' scale(' + CFG.bodyFit.scale + ')';
      g.setAttribute('transform', tr);
      if (src) {{
        for (var i = 0; i < src.childNodes.length; i++) g.appendChild(src.childNodes[i].cloneNode(true));
      }}
      svg.appendChild(g);
    }}
    var holder = document.createElement('div');
    holder.id = 'svg-card-holder';
    holder.appendChild(svg);
    document.body.appendChild(holder);
  }}
  loadFonts().then(function () {{
    if (!CFG.hasVega) return null;
    var el = document.getElementById('chart');
    return vegaEmbed(el, CFG.spec, {{ renderer: 'svg', actions: false }}).then(function () {{
      return el.querySelector('svg');
    }});
  }}).then(function (vegaSvg) {{
    if (CFG.svgCard) svgCard(vegaSvg);
    done(null);
  }}).catch(function (err) {{
    var el = document.getElementById('chart');
    if (el) {{
      var pre = document.createElement('pre');
      pre.className = 'render-error';
      pre.textContent = 'Chart failed to render: ' + (err && err.message || err);
      el.innerHTML = '';
      el.appendChild(pre);
    }}
    done(err || new Error('render failed'));
  }});
}})();
</script>
</body>
</html>
"""


def svg_body_fit(markup: str, box) -> tuple[str, dict | None]:
    """Prepare an SVG file's markup for the chart box: strip the XML prolog, make sure it scales."""
    m = re.sub(r"<\?xml[^>]*\?>", "", markup).strip()
    m = re.sub(r"<!DOCTYPE[^>]*>", "", m).strip()
    head = re.search(r"<svg\b[^>]*>", m)
    fit = None
    if head:
        tag = head.group(0)
        vb = re.search(r"viewBox=[\"']\s*([-\d.]+)[\s,]+([-\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)", tag)
        w = re.search(r"\swidth=[\"']([\d.]+)", tag)
        h = re.search(r"\sheight=[\"']([\d.]+)", tag)
        if vb:
            vw, vh = float(vb.group(3)), float(vb.group(4))
        elif w and h:
            vw, vh = float(w.group(1)), float(h.group(1))
            tag2 = tag[:-1] + f' viewBox="0 0 {vw} {vh}">'
            m = m.replace(tag, tag2, 1)
            tag = tag2
        else:
            vw, vh = box.w, box.h
        if "preserveAspectRatio" not in tag:
            m = m.replace(tag, tag[:-1] + ' preserveAspectRatio="xMidYMid meet">', 1)
        fit = {"scale": round(min(box.w / vw, box.h / vh), 5), "vw": vw, "vh": vh}
    return m, fit
