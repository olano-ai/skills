---
name: image
description: "Use this skill whenever the user wants any kind of image made, edited, checked or optimised — a photo-real scene, an illustration, a cartoon or character, a 3D icon, a product mockup, a blog hero, a social graphic, a quote or stat card, a thumbnail, an OG image, a banner, a diagram, a chart or a poster — and whenever they say 'generate an image', 'make a picture', 'create a graphic', 'hero image', 'cover photo', 'profile banner', 'product mockup', 'image optimisation', 'WebP' or 'OG image'. It is the router for every image request: it decides between image_generate (pictures), render_html_image (anything with words, numbers, logos or a layout), the architecture-diagram skill (diagrams), the charts skill (data charts) and canvas-design (fine-art posters), then covers prompting, QA and delivery for generated pictures."
metadata:
  version: 3.0.0
---

# Image

Every image request lands here first. Decide the genre, hand the words-and-layout half to the browser renderer and the picture half to the image model, check the result once, save it, and say where it is.

## Which tool makes it

| The user wants… | Make it with | Notes |
|---|---|---|
| A photographic scene, lifestyle shot, background, texture | `image_generate` | `image_edit` to fix one region, `image_describe` to QA |
| An illustration, flat/vector-style art, editorial drawing | `image_generate` | Same loop; medium and linework words carry the style |
| A cartoon, mascot or character (one, or a consistent set) | `image_generate` | Write a character sheet once, reuse it in every prompt |
| A 3D icon, glossy object, app-icon-style render | `image_generate` | Material + render-style words, plain backdrop, generous margin |
| A product mockup or device scene | `image_generate` for the scene; the real screenshot is composed in with `render_html_image` | The model never paints the UI |
| Anything with words, numbers, a logo, a layout or a CTA — social graphic, quote card, stat card, thumbnail, OG image, banner, carousel | `render_html_image` via the `social-image-composer` skill | Text is **rendered, never generated**; a generated image is only the artwork layer |
| A diagram (architecture, flow, sequence, org chart) | the `architecture-diagram` skill (Mermaid), or hand-written SVG rendered with `render_html_image` | |
| A data chart (bar, line, pie, KPI tile, table-as-image) | the `charts` skill | Its recipes, Vega-Lite and frame; never draw a chart here |
| A fine-art poster or designed piece | the `canvas-design` skill | Design philosophy first, then the canvas |

Two rules decide almost every case:

1. **If a human is meant to read something on it, that something is HTML.** Image models still misspell, miscount and mis-draw logos, and a wrong letter cannot be fixed without regenerating the whole picture. Generate the picture; render the words over it.
2. **If it plots numbers, it is a chart**, and charts have their own skill. An infographic embeds the chart image the `charts` skill produced; it does not ask the image model to draw axes.

Both renderers run on the Chromium that ships with Olano — no key, no credits — and take either an inline HTML string or a path to an `.html` file in the workspace. `image_generate`, `image_edit` and `image_describe` run on the box's configured image and vision services. Before starting, read `brand/tokens.json` if it exists (the `brand-kit` skill writes it) and the product-marketing context doc if the `product-marketing` skill has produced one; ask only for what neither covers — the destination and its size, the subject, the style.

## Prompting image_generate

`image_generate(prompt, aspect_ratio="1:1", quality="medium", n=1)`. Build the prompt from this template, one clause per line, dropping lines that do not apply:

```
Subject:      what, exactly — one main subject, its state and action
Style:        photograph / flat illustration / watercolor / 3D render / cartoon …
Composition:  framing (close-up, medium, wide), angle, where the empty space goes
Lighting:     the light's direction, quality and colour
Palette:      3–4 colour words, or the brand colours by name
Mood:         two or three adjectives
Negatives:    no text, no words, no lettering, no logos, no watermark, no extra limbs …
```

Then say it as prose, 40–90 words: `[subject], [style], [composition], [lighting], [palette], [mood]. No text, no logos, no watermark.` Piles of adjectives dilute; specific nouns and light words sharpen. Worked prompts for every genre are in [references/prompting.md](references/prompting.md).

### Per-genre patterns

- **Photograph** — camera and lens words (`35mm`, `85mm portrait lens`, `shallow depth of field`), light words (`soft window light from the left`, `golden hour backlight`, `overcast diffuse light`), a real surface or place. Say `photorealistic, editorial photograph`, never "high quality".
- **Illustration** — name the medium and the line (`flat vector illustration, clean 2px linework, four-colour palette, paper-grain texture`) and a reference era or school, not a living artist's name.
- **Cartoon / character** — write a **character sheet** once (species or age, build, face, hair, three signature colours, outfit, one prop) and paste it verbatim into every prompt for that character; add only the pose and expression per image. Consistency comes from repeating the sheet, not from hoping.
- **3D / icon** — material and render words (`matte clay`, `glossy plastic`, `frosted glass`, `soft studio lighting, subtle ambient occlusion, isometric`), one object centred on a plain background in the brand colour, generous margin.
- **Product mockup** — generate only the scene: the desk, the hand, the wall, the device *with a blank dark screen*. Then place the real screenshot over the screen area in HTML and render with `render_html_image`. The model never draws the UI.

### Aspect ratio per destination

`image_generate` accepts `1:1`, `16:9`, `9:16`, `4:3`, `3:4` and `21:9`.

| Destination | Ask for | Then |
|---|---|---|
| Feed post, avatar, icon | `1:1` | use as is (1080×1080) |
| Blog hero, OG image, YouTube thumbnail, slide | `16:9` | a 1200×630 OG image is a 16:9 with a little top and bottom trimmed |
| Story, Reel, TikTok, vertical banner | `9:16` | |
| Portrait feed post (4:5) | `3:4` | compose to 1080×1350 in HTML (`object-fit: cover`) or crop with Pillow |
| Wide banner (LinkedIn cover, X header) | `21:9` | crop to the platform's exact size |

### Settings and iteration

- `quality: "high"` for anything that ships; the default is fine while exploring.
- `n: 1`, then iterate on the prompt. Four variants of a vague prompt are four vague images.
- **Never ask the model to render text or numbers** — not a headline, not a price, not a logo, not a date. Put `no text, no words, no lettering, no logos` in every prompt; models add signage unprompted.
- **One `image_edit` pass fixes a region; regenerating loses what was good.** `image_edit(image, prompt, mask)` — the mask's transparent area is what changes. Use it for a stray object, a wrong colour, a background swap. If the one edit is still wrong, go back to the prompt.
- **Brand palette** — when `brand/tokens.json` exists, turn its palette into colour *words* in the prompt (`deep navy, warm grey, coral accent`); models read colour names better than hex codes. Keep the hex values for the HTML layer.
- Put the destination's safe zones in the composition line: `subject in the upper-left third, empty space across the lower half` leaves room for the words that will be rendered over it.

## QA

One `image_describe` pass per finished image, with fixed questions, then act on the answers:

```
image_describe(image="images/<file>.png", question="Check this image and answer each point briefly: 1) Any visual artifacts — extra limbs or fingers, warped faces, merged objects, floating parts? 2) Any text, letters, numbers or logo-like marks anywhere, and are they garbled? 3) What is the main subject, and does it match: <one-line intent>? 4) Dominant colours — anything off-brand versus <palette words>? 5) Is the subject or any important element cut off at an edge?")
```

- Artifact or garbled text in one region → one `image_edit` with a mask over that region.
- Wrong subject or composition → fix the prompt, regenerate once.
- Off-brand colour → palette words in the prompt, or a colour overlay in the HTML layer.
- Cut off at an edge → `generous margin around the subject` in the composition line, or a wider aspect ratio.

For rendered graphics (`render_html_image`) ask instead: is every word legible and spelled correctly, is the logo clean, does anything touch the canvas edge — the `social-image-composer` skill holds that checklist. Then look at the image yourself before handing it over.

## Marketing workflows

### Blog and article hero

1. Concept — the visual metaphor for the topic, one sentence.
2. `image_generate` at `16:9`, `quality: "high"`, no text; the composition leaves space where a title would sit if the site overlays one.
3. Title on the image itself? Compose it: the picture as `background-image`, the headline in HTML, `render_html_image(width=1200, height=630)` — the same file serves as the OG image.
4. Deliver at the display size (1920×1080 full-width, 1200×630 OG); optimise per "Format and size" below.

### Social graphics

Anything with a headline, a number, a handle or a logo is the `social-image-composer` skill: brand tokens → HTML at the platform's exact size → `render_html_image` (`scale: 2` for retina) → `image_describe`. This skill's part is the artwork layer underneath, generated at the matching aspect ratio with the empty space where the type will go. A pure picture post (no words) is `image_generate` + QA + delivery.

| Platform | Size | Ratio |
|---|---|---|
| X / Twitter | 1200×675 | 16:9 |
| LinkedIn feed | 1200×627 | 1.91:1 |
| Instagram feed | 1080×1080 / 1080×1350 | 1:1 / 4:5 |
| Stories / Reels / TikTok | 1080×1920 | 9:16 |
| Facebook link | 1200×630 | 1.91:1 |

### Product mockups and screenshots

Models hallucinate interfaces — never generate the UI. Capture the real screen (the `browser-use` skill's screenshot at 2× for a web app, or the user's own capture), then compose: a generated or pure-CSS scene with a device frame drawn in HTML, the screenshot inside it with `object-fit: cover`, callouts and labels as HTML — and `render_html_image` at the target size. A before/after is two frames side by side in one HTML file.

### Profile and listing banners

| Platform | Size | Notes |
|---|---|---|
| LinkedIn personal cover | 1584×396 | keep the centre clear of the avatar |
| LinkedIn company cover | 1128×191 | |
| X header | 1500×500 | lower-left hidden by the avatar |
| GitHub social preview | 1280×640 | |
| Product Hunt gallery | 1270×760 | real screenshots, light annotation |
| Google Play feature graphic | 1024×500 | |

Generate the backdrop at `21:9` (`16:9` for the squarer ones) with the subject off to one side, then compose tagline, logo and product shot in HTML at the exact size. Banners are seen small: few words, critical content in the centre, check at 25% zoom.

### OG and social preview images

1200×630 (1.91:1), one per page. A static page gets the hero composition above. Many pages (posts, profiles) get one HTML template with the title and author as variables, rendered per page with `render_html_image(width=1200, height=630)` — a hundred pages is a loop, not a design task. Wire the tags:

```html
<meta property="og:image" content="https://yoursite.com/og/page-name.png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta name="twitter:card" content="summary_large_image" />
```

### Brand assets

| Asset | Route |
|---|---|
| Logo | not a generation task — hand-written SVG (or the user's file); `image_generate` for mood boards only |
| App icon | `image_generate` at `1:1` for concepts (the 3D/icon pattern), then a clean SVG or a masked render for the final |
| Illustration set | one style prompt plus the character-sheet trick for consistency; generate and QA each |
| Favicon | derive from the logo SVG, render at 32/64/180 px with `render_html_image` |

## Format and size

| Format | Use for | Notes |
|---|---|---|
| **PNG** | rendered graphics, screenshots, anything with text or transparency | lossless; large for photos |
| **JPEG** | photographs with no transparency | quality 80–85 is the sweet spot |
| **WebP** | the web-serving copy of either | 25–35% smaller; ~96% browser support — keep the PNG/JPEG original |
| **SVG** | logos, icons, diagrams | vector; rasterise to PNG only for platforms that need it |

Size it right up front: `render_html_image` renders at exactly `width` × `height` (`scale: 2` doubles the pixels for retina) and `image_generate`'s aspect ratio picks the crop. Never upscale a small render — re-render larger.

Optimising an existing file (Pillow is present on the host lane; on the sandbox `python3 -m pip install --user pillow` once):

```python
from PIL import Image
im = Image.open("images/hero.png").convert("RGB")
im.thumbnail((1920, 1920))                      # never enlarges; keeps the aspect ratio
im.save("reports/hero.jpg", "JPEG", quality=82, optimize=True, progressive=True)
im.save("reports/hero.webp", "WEBP", quality=80, method=6)
```

Aim under 200 KB for a hero and under 100 KB for an OG image; keep transparency (PNG/WebP) only where it is used. When the source is a PDF, `pdftoppm` renders pages and `pdfimages` extracts embedded images (poppler, present everywhere).

## Delivery

- Save under `reports/` — or `images/`, where `image_generate` writes its own files (`renders/` is where the render tools default when no `save_path` is given). Descriptive names: `reports/hero-onboarding-1200x630.png`.
- Keep the prompt, or the HTML, next to any deliverable that may need a second version — a re-render takes seconds, a regeneration is a lottery.
- Finish with the path on its own line: `Saved: <path>` — one line per file when there are several.

## Related skills

- `social-image-composer` — the HTML-over-artwork graphic with text, logos and CTAs
- `charts` — every data chart
- `architecture-diagram` — Mermaid diagrams
- `canvas-design` — fine-art posters and designed pieces with the bundled fonts
- `brand-kit` — the palette, fonts and logo every graphic is built from
- `social` / `social-campaign` — what to post and the campaign around it
- `browser-use` — real screenshots for mockups
- `pdf` — page renders from documents
