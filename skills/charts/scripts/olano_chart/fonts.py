"""Font discovery, ``@font-face`` embedding and text measurement — standard library only.

The bundled OFL fonts live in the sibling ``canvas-design`` skill
(``<skills>/canvas-design/canvas-fonts``).  They are resolved relative to this
file at runtime, overridable with ``OLANO_FONTS_DIR``; when the directory is
absent every family falls back to the system UI stack and measurement falls
back to a per-family average glyph width.

Faces are inlined into the page as base64 data URIs so rendering never depends
on a ``file://`` font policy, and the TrueType ``hmtx``/``cmap`` tables are
parsed here so Python can measure a label to the pixel *before* Vega runs —
that is what decides whether a value fits inside a bar and how a title wraps.
"""
from __future__ import annotations

import base64
import os
import struct
from dataclasses import dataclass, field
from pathlib import Path

FALLBACK_SANS = 'system-ui, -apple-system, "Segoe UI", sans-serif'
FALLBACK_SERIF = 'Georgia, "Times New Roman", serif'
FALLBACK_MONO = 'ui-monospace, "SF Mono", Menlo, Consolas, monospace'

# Average advance width as a fraction of the em, used only when a face cannot
# be measured (missing file or a family we do not bundle).
_HEURISTIC_WIDTH = {"sans": 0.54, "sans-bold": 0.58, "serif": 0.46, "mono": 0.60, "condensed": 0.42}


def fonts_dir() -> Path | None:
    """Directory holding the bundled ``.ttf`` files, or ``None`` when unavailable."""
    env = os.environ.get("OLANO_FONTS_DIR")
    if env:
        p = Path(env).expanduser()
        return p if p.is_dir() else None
    here = Path(__file__).resolve()
    # scripts/olano_chart/fonts.py -> parents[3] is the skills/ directory.
    if len(here.parents) > 3:
        candidate = here.parents[3] / "canvas-design" / "canvas-fonts"
        if candidate.is_dir():
            return candidate
    return None


@dataclass(frozen=True)
class FontFace:
    family: str
    weight: int = 400
    style: str = "normal"
    path: Path | None = None  # None -> not available on this box

    @property
    def available(self) -> bool:
        return self.path is not None and self.path.is_file()


@dataclass
class FontSet:
    """The faces one theme uses, plus the CSS family stacks to write."""

    faces: list[FontFace] = field(default_factory=list)
    stacks: dict[str, str] = field(default_factory=dict)  # role -> CSS font-family value

    def css_stack(self, role: str) -> str:
        return self.stacks.get(role, FALLBACK_SANS)

    def available_faces(self) -> list[FontFace]:
        return [f for f in self.faces if f.available]

    def load_descriptors(self) -> list[str]:
        """``document.fonts.load()`` strings — one per embedded face."""
        return [f'{"italic " if f.style == "italic" else ""}{f.weight} 16px "{f.family}"' for f in self.available_faces()]


def resolve_font_file(file: str | None) -> Path | None:
    """Absolute path for a theme/brand font file, or ``None``.

    ``file`` may be absolute, relative to the current directory (brand kits), or a
    bare file name inside the bundled fonts directory.
    """
    if not file:
        return None
    p = Path(file).expanduser()
    if p.is_absolute() and p.is_file():
        return p
    if p.is_file():
        return p.resolve()
    d = fonts_dir()
    if d is not None and (d / p.name).is_file():
        return d / p.name
    return None


def build_fontset(font_roles: dict, generic: dict[str, str] | None = None) -> FontSet:
    """Turn a theme's ``fonts`` block into a :class:`FontSet`.

    ``font_roles`` maps a role (``display``/``body``/``numeric``/``annotation``)
    to ``{"family": str, "generic": "sans|serif|mono", "faces": [{"file", "weight", "style"}]}``.
    """
    faces: dict[tuple[str, int, str], FontFace] = {}
    stacks: dict[str, str] = {}
    for role, spec in font_roles.items():
        family = spec.get("family", "")
        gen = spec.get("generic", "sans")
        fallback = {"serif": FALLBACK_SERIF, "mono": FALLBACK_MONO}.get(gen, FALLBACK_SANS)
        any_face = False
        for face in spec.get("faces", []):
            path = resolve_font_file(face.get("file"))
            ff = FontFace(family, int(face.get("weight", 400)), face.get("style", "normal"), path)
            key = (ff.family, ff.weight, ff.style)
            if key not in faces or (not faces[key].available and ff.available):
                faces[key] = ff
            any_face = any_face or ff.available
        stacks[role] = f'"{family}", {fallback}' if (family and any_face) else fallback
    return FontSet(list(faces.values()), stacks)


def font_face_css(faces: list[FontFace]) -> str:
    """``@font-face`` rules with the font bytes inlined as data URIs."""
    rules = []
    for f in faces:
        if not f.available:
            continue
        data = base64.b64encode(f.path.read_bytes()).decode("ascii")
        rules.append(
            f'@font-face{{font-family:"{f.family}";font-weight:{f.weight};font-style:{f.style};'
            f'font-display:block;src:url(data:font/ttf;base64,{data}) format("truetype");}}'
        )
    return "\n".join(rules)


# ---------------------------------------------------------------------------
# TrueType measurement
# ---------------------------------------------------------------------------
class _TrueType:
    """Just enough of a TrueType parser to measure text: ``head``, ``hhea``, ``hmtx``, ``cmap``."""

    def __init__(self, path: Path):
        data = path.read_bytes()
        (num_tables,) = struct.unpack(">H", data[4:6])
        tables: dict[str, tuple[int, int]] = {}
        for i in range(num_tables):
            off = 12 + 16 * i
            tag = data[off : off + 4].decode("latin-1")
            toff, tlen = struct.unpack(">II", data[off + 8 : off + 16])
            tables[tag] = (toff, tlen)
        head = tables["head"][0]
        (self.upem,) = struct.unpack(">H", data[head + 18 : head + 20])
        hhea = tables["hhea"][0]
        self.ascent, self.descent, self.line_gap = struct.unpack(">hhh", data[hhea + 4 : hhea + 10])
        (nhm,) = struct.unpack(">H", data[hhea + 34 : hhea + 36])
        hmtx = tables["hmtx"][0]
        self.advances = [struct.unpack(">H", data[hmtx + 4 * i : hmtx + 4 * i + 2])[0] for i in range(nhm)]
        self.cmap = self._parse_cmap(data, tables["cmap"][0])
        # A plausible width for characters the font lacks.
        self.avg = sum(self.advances) / max(1, len(self.advances))

    @staticmethod
    def _parse_cmap(data: bytes, base: int) -> dict[int, int]:
        (n,) = struct.unpack(">H", data[base + 2 : base + 4])
        records = []
        for i in range(n):
            pid, eid, off = struct.unpack(">HHI", data[base + 4 + 8 * i : base + 12 + 8 * i])
            records.append((pid, eid, base + off))
        # Prefer a full-Unicode format-12 subtable, then the BMP format-4 one.
        for want in ((3, 10), (0, 4), (0, 6), (3, 1), (0, 3), (0, 2), (0, 1), (0, 0)):
            for pid, eid, off in records:
                if (pid, eid) == want:
                    (fmt,) = struct.unpack(">H", data[off : off + 2])
                    if fmt == 12:
                        return _TrueType._cmap12(data, off)
                    if fmt == 4:
                        return _TrueType._cmap4(data, off)
        for pid, eid, off in records:  # last resort: any format-4/12 subtable
            (fmt,) = struct.unpack(">H", data[off : off + 2])
            if fmt == 12:
                return _TrueType._cmap12(data, off)
            if fmt == 4:
                return _TrueType._cmap4(data, off)
        return {}

    @staticmethod
    def _cmap4(data: bytes, off: int) -> dict[int, int]:
        (seg_x2,) = struct.unpack(">H", data[off + 6 : off + 8])
        seg = seg_x2 // 2
        ends = struct.unpack(f">{seg}H", data[off + 14 : off + 14 + seg_x2])
        starts_off = off + 16 + seg_x2
        starts = struct.unpack(f">{seg}H", data[starts_off : starts_off + seg_x2])
        deltas_off = starts_off + seg_x2
        deltas = struct.unpack(f">{seg}h", data[deltas_off : deltas_off + seg_x2])
        ranges_off = deltas_off + seg_x2
        ranges = struct.unpack(f">{seg}H", data[ranges_off : ranges_off + seg_x2])
        out: dict[int, int] = {}
        for i in range(seg):
            start, end = starts[i], ends[i]
            if start == 0xFFFF:
                continue
            for c in range(start, min(end, 0xFFFE) + 1):
                if ranges[i] == 0:
                    g = (c + deltas[i]) & 0xFFFF
                else:
                    addr = ranges_off + 2 * i + ranges[i] + 2 * (c - start)
                    if addr + 2 > len(data):
                        continue
                    (g,) = struct.unpack(">H", data[addr : addr + 2])
                    if g:
                        g = (g + deltas[i]) & 0xFFFF
                if g:
                    out[c] = g
        return out

    @staticmethod
    def _cmap12(data: bytes, off: int) -> dict[int, int]:
        (ngroups,) = struct.unpack(">I", data[off + 12 : off + 16])
        out: dict[int, int] = {}
        p = off + 16
        for _ in range(ngroups):
            s, e, g = struct.unpack(">III", data[p : p + 12])
            p += 12
            for c in range(s, min(e, 0x10FFFF) + 1):
                out[c] = g + (c - s)
        return out

    def width(self, text: str, size: float) -> float:
        total = 0.0
        for ch in text:
            g = self.cmap.get(ord(ch))
            if g is None:
                total += self.avg if ch != " " else self.advances[self.cmap.get(32, 0)] if self.cmap.get(32) is not None else self.avg
                continue
            total += self.advances[g] if g < len(self.advances) else self.advances[-1]
        return total * size / self.upem


_TTF_CACHE: dict[Path, _TrueType | None] = {}


def _ttf(path: Path | None) -> _TrueType | None:
    if path is None:
        return None
    if path not in _TTF_CACHE:
        try:
            _TTF_CACHE[path] = _TrueType(path)
        except Exception:  # a font we cannot parse still renders; we just estimate widths
            _TTF_CACHE[path] = None
    return _TTF_CACHE[path]


class Measurer:
    """Measures text in the faces of one :class:`FontSet`, with a heuristic fallback."""

    def __init__(self, fontset: FontSet, generic_by_family: dict[str, str] | None = None):
        self.fontset = fontset
        self.generic = generic_by_family or {}

    def _face(self, family: str, weight: int, style: str) -> FontFace | None:
        best, best_d = None, 10**9
        for f in self.fontset.faces:
            if f.family != family or not f.available:
                continue
            d = abs(f.weight - weight) + (0 if f.style == style else 150)
            if d < best_d:
                best, best_d = f, d
        return best

    def width(self, text: str, family: str, size: float, weight: int = 400, style: str = "normal",
              letter_spacing_em: float = 0.0) -> float:
        """Advance width in px, unkerned (a slight over-estimate — safe for wrapping)."""
        face = self._face(family, weight, style)
        ttf = _ttf(face.path) if face else None
        if ttf is not None:
            w = ttf.width(text, size)
        else:
            gen = self.generic.get(family, "sans")
            key = "sans-bold" if (gen == "sans" and weight >= 600) else gen
            w = len(text) * size * _HEURISTIC_WIDTH.get(key, 0.55)
        return w + letter_spacing_em * size * max(0, len(text) - 1)

    def metrics(self, family: str, weight: int = 400, style: str = "normal") -> tuple[float, float]:
        """(ascent, descent) as fractions of the em (descent positive)."""
        face = self._face(family, weight, style)
        ttf = _ttf(face.path) if face else None
        if ttf is None:
            return 0.92, 0.24
        return ttf.ascent / ttf.upem, abs(ttf.descent) / ttf.upem

    def wrap(self, text: str, max_width: float, family: str, size: float, weight: int = 400,
             style: str = "normal", letter_spacing_em: float = 0.0, max_lines: int | None = None) -> list[str]:
        """Greedy word wrap; explicit newlines always break. Never returns an empty list."""
        lines: list[str] = []
        for para in (text or "").split("\n"):
            words = para.split()
            if not words:
                lines.append("")
                continue
            cur = words[0]
            for w in words[1:]:
                trial = f"{cur} {w}"
                if self.width(trial, family, size, weight, style, letter_spacing_em) <= max_width:
                    cur = trial
                else:
                    lines.append(cur)
                    cur = w
            lines.append(cur)
        if max_lines is not None and len(lines) > max_lines:
            head = lines[: max_lines - 1]
            tail = " ".join(lines[max_lines - 1 :])
            # Truncate the last line with an ellipsis so nothing ever overflows the block.
            while tail and self.width(tail + "…", family, size, weight, style, letter_spacing_em) > max_width:
                tail = tail[:-1].rstrip()
            lines = head + [tail + "…"]
        return lines or [""]
