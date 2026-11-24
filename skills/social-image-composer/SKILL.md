---
name: social-image-composer
description: "Produce branded social graphics and carousels at exact platform dimensions by composing HTML/CSS over generated artwork. Use this skill whenever the user wants a social image, post graphic, carousel, quote card, stat card, announcement graphic, LinkedIn document post, Instagram carousel, story graphic, YouTube thumbnail, OG image, or asks to 'make a graphic,' 'design a post,' 'turn this into slides,' 'add the headline to that image,' 'put our logo on it,' or 'resize it for LinkedIn.' Use it whenever a graphic needs readable text, a logo, a statistic, a screenshot or a CTA on it — a generated image alone cannot set type reliably. Do NOT use it for fine-art posters or illustration (see canvas-design), or for generating a photograph or scene with no text (call image_generate directly)."
metadata:
  requires_tools: [render_html_image, image_generate]
---

# Social Image Composer

Image models have got good at pictures and stayed bad at typography. Ask one for
a post graphic with a headline and you get plausible-looking letters that spell
something else, a logo that is nearly your logo, and a number that is nearly
your number — and you cannot fix any of it without regenerating the whole
picture and losing what was good about it.

So split the job. The model paints what it is good at: the photograph, the
texture, the abstract field, the visual metaphor. Everything a human is meant to
*read* — headline, statistic, logo, CTA, handle, legal line — is set in HTML and
CSS and rendered by a real browser at exact pixel dimensions. Change the
headline later and you re-render in a second; the artwork does not move.

## The two tools

| Tool | Use for |
|---|---|
| `render_html_image` | One PNG at exact dimensions. `scale: 2` exports retina |
| `render_html_pdf` | Multi-page PDF — a LinkedIn native document (carousel) post |

Both run on the Chromium that ships with Olano: no API key, no network, nothing
billed. `image_generate` supplies the artwork layer; `image_describe` reads the
finished PNG back for the quality check at the end.

## Before anything else: load the brand kit

Read `<workspace>/brand/tokens.json`. It carries the palette, the font families
*and their file paths*, the type scale, the safe padding and the logo. If it is
missing, invoke `brand-kit` first — a graphic in an invented blue is a graphic
that gets thrown away.

Turn the tokens into CSS custom properties at `:root` once, then use the
variables everywhere. `references/tokens-schema.md` in the `brand-kit` skill has
the exact mapping, including the `@font-face` rule — which needs an absolute
`file://` URL, or the card silently renders in fallback sans.

## Dimensions

Author at the logical size in this table and export at `scale: 2`. Never
double these numbers yourself.

| Placement | Canvas | Notes |
|---|---|---|
| Instagram / LinkedIn square | 1080 × 1080 | The safe default when unsure |
| Instagram / LinkedIn portrait | 1080 × 1350 | 4:5 — the most feed real estate |
| LinkedIn / X / Facebook link card | 1200 × 628 | 1.91:1. Text ≥ 40px or it is unreadable in-feed |
| X in-feed image | 1600 × 900 | 16:9 |
| Story / Reel / TikTok | 1080 × 1920 | 9:16 |
| LinkedIn carousel (PDF) | 1080 × 1350 per page | Native document post |
| Instagram carousel (PNG set) | 1080 × 1350 each | One file per slide, numbered |
| YouTube thumbnail | 1280 × 720 | Legible at 210 × 118 — that is the real test |

**Safe zones are not optional.** Platforms crop and overlay their own UI:

- **Story / Reel / TikTok**: keep everything meaningful out of the top 250px and
  the bottom 400px. The bottom band is where captions, the handle and the
  controls sit.
- **Instagram feed**: the square crop of a 4:5 image is what shows on a profile
  grid. Nothing load-bearing in the bottom 270px.
- **Link cards**: assume 5–8% gets clipped on some client. Keep to the padding.

## Building a single graphic

### 1. Decide whether it needs artwork at all

Plenty of the best social graphics are type on a flat field. A generated
background earns its place when it adds a scene, a texture or a metaphor — not
when it is decoration behind a headline it makes harder to read. If in doubt,
build the type-only version first; it takes seconds and is often the one that
ships.

### 2. Generate the artwork layer, if any

Call `image_generate` with an `aspect_ratio` matching the canvas, and prompt for
**a background, not a poster**: describe the scene, the light, the palette, the
composition — and say where the empty space goes.

> Good: "Wide overhead shot of an empty modern workshop bench, cool morning
> light from the left, deep navy and warm grey, generous empty space across the
> lower two-thirds, no text, no logos, no people."

> Bad: "A LinkedIn post graphic saying 'We raised $4M' with our logo."

Say "no text, no words, no lettering" explicitly. Models add signage unprompted,
and misspelled signage in the background is worse than no background.

### 3. Compose

Write an HTML file into the workspace and reference the artwork with a relative
`<img>` or `background-image`. Writing it into the workspace root (rather than
passing a giant inline string) makes it re-renderable after a copy tweak and
keeps relative asset paths honest.

A working single-card skeleton is in `references/templates.md`, along with the
overlay recipe that keeps text readable on any photograph — a scrim gradient
rather than a flat opacity wash, so the image stays visible where there is no
type over it.

Then:

```
render_html_image(html="cards/announcement.html", width=1080, height=1350,
                  scale=2, save_path="renders/announcement.png")
```

### 4. Check it

Call `image_describe` on the rendered PNG and ask specifically:

- Is every word legible, and correctly spelled?
- Does anything touch or cross the canvas edge?
- Is anything meaningful inside a platform safe zone?
- Does the logo read cleanly at this size?

Then look at it yourself. A render is fast; shipping a broken one is not. Fix by
editing the HTML and re-rendering — never by regenerating the artwork.

## Building a carousel

A carousel is one narrative, not a set of graphics that share a palette. Six to
eight slides is the working range.

```
1  Hook       Stands alone. If nobody swipes, this slide still has to land
2  Problem    Name the thing the reader recognises
3–6 Body      One idea per slide. One sentence, one number, one visual
7  Payoff     The insight the whole thing was building toward
8  CTA        One specific ask. Not three
```

Author **all slides in one HTML document**, each in a `.slide` div sized to the
canvas, sharing one `:root` token block. That is what keeps slide 6 looking like
slide 1.

**LinkedIn — one PDF:**

```
render_html_pdf(html="carousel.html", width=1080, height=1350,
                save_path="renders/carousel.pdf")
```

Each `.slide` needs `page-break-after: always` — that is what makes one page per
slide. Verify the page count before handing it over; a carousel that rendered as
one long page is a common and silent failure.

**Instagram / TikTok — a numbered PNG set:** render the same document once per
slide by adding a body class that shows only slide *n* (the pattern is in
`references/templates.md`), saving to `renders/slide-01.png` … `slide-08.png`.
Zero-pad the numbers so they upload in order.

## Resizing an existing graphic

Do not scale a finished PNG — text goes soft and the composition breaks. Re-render
the same HTML at the new canvas, adjusting only the type scale and the line
breaks. That is the point of keeping the source: a square, a portrait and a story
are three renders of one document, not three designs.

## Common failures

**Fallback font.** The card renders in Helvetica and looks generic. The
`@font-face` `src` needs an absolute `file://` URL when the font is outside the
workspace. Check the render, not the CSS.

**Text over a busy photo.** Contrast passes in one corner and fails in another.
Use the scrim gradient from the templates, or move the type onto a solid panel.

**Headline overflow.** A long headline pushes past the canvas. Set an explicit
`font-size` from the token scale rather than a viewport unit, and check the
render — CSS will happily lay out beyond the edge without complaining.

**Everything centred.** Centred type, a centred logo and a centred CTA is the
house style of generated design. Anchor the composition to one edge and let the
whitespace be uneven.

**Gradient plus rounded corners plus a soft shadow.** The three tells. Pick one
if any.

## Reference files

- `references/templates.md` — working HTML skeletons: single card, photo overlay
  with scrim, stat card, quote card, and the multi-slide carousel document with
  the per-slide export pattern. Read it before writing the first template.
