# `tokens.json` schema

The machine-readable half of the brand kit. `social-image-composer` reads this
file to build HTML, so every field here exists because a renderer needs it —
there is no decorative metadata.

Write it to `<workspace>/brand/tokens.json`.

## Contents

- [Schema](#schema)
- [Field notes](#field-notes)
- [Worked example](#worked-example)
- [Consuming it in HTML](#consuming-it-in-html)

## Schema

```jsonc
{
  "version": 1,                    // bump on any substantive change
  "brand": "Acme",                 // display name
  "updated": "2026-08-26",
  "changelog": [                   // newest first, one line each
    "2026-08-26 v1 — initial kit from the marketing site"
  ],

  "palette": {
    "light": {                     // required
      "background": "#FFFFFF",
      "surface":    "#F4F6F8",     // optional
      "text":       "#0B1520",
      "muted":      "#5A6B7B",     // optional
      "accent":     "#E0452C"
    },
    "dark": { }                    // optional, same keys
  },

  "typography": {
    "display": {
      "family":   "Big Shoulders",
      "fallback": "Impact, 'Arial Narrow', sans-serif",
      "file":     "/abs/path/to/BigShoulders-Bold.ttf",   // "" for a system font
      "weight":   700,
      "tracking": "-0.02em"        // optional
    },
    "body": {
      "family":   "Work Sans",
      "fallback": "-apple-system, Segoe UI, Roboto, sans-serif",
      "file":     "/abs/path/to/WorkSans-Regular.ttf",
      "weight":   400
    },
    "scale": {                     // px, at the canvas's LOGICAL size
      "headline": 96,
      "subhead":  48,
      "body":     32,
      "caption":  22
    }
  },

  "layout": {
    "padding": 96,                 // px of margin inside the canvas edge
    "radius":  24,                 // px corner radius on cards/panels
    "gap":     32                  // px between stacked elements
  },

  "logo": {
    "primary": "brand/logo/logo.svg",        // on light backgrounds
    "inverse": "brand/logo/logo-white.svg",  // on dark backgrounds, optional
    "mark":    "brand/logo/mark.svg",        // square/icon lockup, optional
    "min_width": 160                         // px — never render it smaller
  },

  "handles": {                     // optional; used in footers and CTAs
    "site":     "acme.com",
    "linkedin": "acme",
    "x":        "acmehq"
  }
}
```

## Field notes

**`palette` roles are functional, not decorative.** A renderer asks "what goes
behind the slide" and "what is the one thing that should catch the eye" — it
does not ask for "Acme Coral." Keep the role keys exactly as named; add brand
names in a comment or a separate field if you want them recorded.

**`text` on `background` must clear 4.5:1** and `muted` must clear 3:1. Check
when you write the file, not when someone complains a caption is unreadable.

**`typography.*.file` is the field that actually matters.** A `family` with no
`file` renders as the fallback on the rendering box. If the brand's font is not
licensed for embedding or not present, either point at one of the bundled
SIL-licensed faces in the `canvas-design` skill's `canvas-fonts/` directory or
set `file: ""` and pick a `family` the fallback stack can genuinely satisfy.
Absolute paths are safest; relative paths resolve against the workspace.

**`typography.scale` is in logical px.** Author a 1080×1350 card at these sizes
and export at `scale: 2` for retina — do not double the numbers here.

**`layout.padding` is the safe margin.** Platforms crop and overlay: Instagram
puts UI in the bottom band, TikTok puts controls over the lower fifth. 80–120px
on a 1080px canvas is the working range.

**`logo.min_width`** stops a lockup being scaled down until the wordmark closes
up. If you only have a raster logo, supply the largest version you have — the
renderer can scale down cleanly, never up.

## Worked example

A complete, valid file using only fonts that ship on every Olano box:

```json
{
  "version": 2,
  "brand": "Acme",
  "updated": "2026-08-26",
  "changelog": [
    "2026-08-26 v2 — accent moved to #E0452C after the rebrand",
    "2026-07-02 v1 — initial kit from acme.com"
  ],
  "palette": {
    "light": {
      "background": "#FFFFFF",
      "surface": "#F4F6F8",
      "text": "#0B1520",
      "muted": "#5A6B7B",
      "accent": "#E0452C"
    },
    "dark": {
      "background": "#0B1520",
      "surface": "#152435",
      "text": "#F4F6F8",
      "muted": "#8FA3B5",
      "accent": "#FF6A4D"
    }
  },
  "typography": {
    "display": {
      "family": "Big Shoulders",
      "fallback": "Impact, 'Arial Narrow', sans-serif",
      "file": "/root/.olano/skills/canvas-design/canvas-fonts/BigShoulders-Bold.ttf",
      "weight": 700,
      "tracking": "-0.01em"
    },
    "body": {
      "family": "Work Sans",
      "fallback": "-apple-system, 'Segoe UI', Roboto, sans-serif",
      "file": "/root/.olano/skills/canvas-design/canvas-fonts/WorkSans-Regular.ttf",
      "weight": 400
    },
    "scale": { "headline": 96, "subhead": 48, "body": 32, "caption": 22 }
  },
  "layout": { "padding": 96, "radius": 24, "gap": 32 },
  "logo": {
    "primary": "brand/logo/logo.svg",
    "inverse": "brand/logo/logo-white.svg",
    "min_width": 160
  },
  "handles": { "site": "acme.com", "linkedin": "acme", "x": "acmehq" }
}
```

## Consuming it in HTML

Tokens become CSS custom properties. Declaring them once at `:root` means a
palette change is one edit rather than a search-and-replace through every
template:

```html
<style>
  @font-face {
    font-family: "Big Shoulders";
    src: url("file:///root/.olano/skills/canvas-design/canvas-fonts/BigShoulders-Bold.ttf")
         format("truetype");
    font-weight: 700;
  }
  :root {
    --bg: #FFFFFF; --surface: #F4F6F8; --text: #0B1520;
    --muted: #5A6B7B; --accent: #E0452C;
    --display: "Big Shoulders", Impact, "Arial Narrow", sans-serif;
    --body: "Work Sans", -apple-system, "Segoe UI", Roboto, sans-serif;
    --pad: 96px; --radius: 24px; --gap: 32px;
  }
</style>
```

Two things break silently here, so check both:

- **`@font-face` needs an absolute `file://` URL** when the font lives outside
  the workspace. A bare relative path resolves against the HTML file's own
  directory and fails quietly to the fallback.
- **A logo path in `tokens.json` is workspace-relative**; in the HTML it must
  resolve from wherever the document sits. Writing the HTML into the workspace
  root keeps both spellings the same.
