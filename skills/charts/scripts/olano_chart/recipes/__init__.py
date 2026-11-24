"""Recipes: one small, flat ``build(spec, theme) -> dict`` per chart type.

Each module is meant to be copied and forked (``--recipe my_recipe.py``).  A
recipe returns a Vega-Lite spec *without* ``$schema``/``config``/``width``/
``height`` — ``chart.py`` adds those from the theme and the layout — and may
declare three optional hooks:

- ``SUPPORTS_ANNOTATIONS = True``      annotations are drawn beside their target
                                       (otherwise they become captions under the chart)
- ``preferred_height(spec, scale, w)`` cap the chart height (five bars want less than 800px)
- ``has_chart(spec)``                  ``False`` when nothing should be drawn (a stat card without a sparkline)
"""
from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from types import ModuleType

RECIPES = ("bar", "column", "stacked_bar", "grouped_bar", "line", "area", "dumbbell", "donut",
           "stat", "histogram", "heatmap", "scatter")


def load_recipe(type_name: str, custom_path: str | Path | None = None) -> ModuleType:
    """The built-in module for ``type_name``, or a custom module loaded from a file."""
    if custom_path:
        p = Path(custom_path)
        if not p.is_file():
            raise ValueError(f"--recipe file not found: {p}")
        mod_spec = importlib.util.spec_from_file_location(f"olano_custom_recipe_{p.stem}", p)
        if mod_spec is None or mod_spec.loader is None:
            raise ValueError(f"cannot import recipe module {p}")
        mod = importlib.util.module_from_spec(mod_spec)
        mod_spec.loader.exec_module(mod)
        if not callable(getattr(mod, "build", None)):
            raise ValueError(f"{p} must define build(spec, theme) -> dict (copy a module from scripts/olano_chart/recipes/ to start)")
        return mod
    if type_name not in RECIPES:
        raise ValueError(f"no recipe for type '{type_name}' — one of {', '.join(RECIPES)}")
    return importlib.import_module(f"{__name__}.{type_name}")
