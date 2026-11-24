"""olano_chart — recipe JSON (or any Vega-Lite spec) → themed, self-contained HTML chart card.

Standard library only.  Entry point: ``scripts/chart.py``.  Modules:

- ``spec``     recipe JSON → validated dataclasses with actionable errors
- ``layout``   size presets, type scale, chrome geometry, label-fit rules
- ``themes``   theme tokens, the ``brand`` override, the Vega-Lite config
- ``palette``  the palette checks (shared with ``scripts/validate_palette.py``)
- ``fonts``    bundled-font discovery, data-URI @font-face, TrueType measurement
- ``frame``    the HTML page (chrome + Vega + ``.render-done``) and the SVG card
- ``recipes``  one small ``build(spec, theme) -> dict`` per chart type
"""

__version__ = "1.0.0"
