# HTML templates for social graphics

Working skeletons. Every one assumes a `:root` token block built from
`<workspace>/brand/tokens.json` — see the `brand-kit` skill's
`references/tokens-schema.md` for that mapping.

## Contents

- [The shared stylesheet](#the-shared-stylesheet)
- [Single card](#single-card)
- [Photo card with a scrim](#photo-card-with-a-scrim)
- [Stat card](#stat-card)
- [Quote card](#quote-card)
- [Carousel](#carousel)
- [Story / Reel safe zones](#story--reel-safe-zones)

## The shared stylesheet

Write this once to `<workspace>/brand/cards.css` and `<link>` it from every
card. One stylesheet is what makes eight carousel slides look like one
carousel, and it means a palette correction is a single edit.

```css
/* brand/cards.css — generated from brand/tokens.json */
@font-face {
  font-family: "Big Shoulders";
  src: url("file:///root/.olano/skills/canvas-design/canvas-fonts/BigShoulders-Bold.ttf")
       format("truetype");
  font-weight: 700;
}
@font-face {
  font-family: "Work Sans";
  src: url("file:///root/.olano/skills/canvas-design/canvas-fonts/WorkSans-Regular.ttf")
       format("truetype");
  font-weight: 400;
}

:root {
  --bg: #FFFFFF;
  --surface: #F4F6F8;
  --text: #0B1520;
  --muted: #5A6B7B;
  --accent: #E0452C;
  --display: "Big Shoulders", Impact, "Arial Narrow", sans-serif;
  --body: "Work Sans", -apple-system, "Segoe UI", Roboto, sans-serif;
  --pad: 96px;
  --radius: 24px;
  --gap: 32px;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

/* Every card is exactly the canvas. `overflow: hidden` is the guard that turns
   an overflowing headline into a visible clip instead of a silently taller
   page that the screenshot then crops somewhere arbitrary. */
.card {
  width: var(--w);
  height: var(--h);
  padding: var(--pad);
  background: var(--bg);
  color: var(--text);
  font-family: var(--body);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.headline {
  font-family: var(--display);
  font-size: 96px;
  line-height: 1.02;
  letter-spacing: -0.01em;
  text-transform: uppercase;
}
.subhead { font-size: 48px; line-height: 1.25; }
.body    { font-size: 32px; line-height: 1.45; }
.caption { font-size: 22px; color: var(--muted); }
.accent  { color: var(--accent); }
.spacer  { flex: 1; }

.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--gap);
}
.footer img { height: 48px; width: auto; }
```

The `--w` / `--h` variables are set per file, so one stylesheet serves every
canvas size.

## Single card

```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="brand/cards.css">
  <style>:root { --w: 1080px; --h: 1350px; }</style>
</head>
<body>
  <div class="card">
    <p class="caption">Product update</p>
    <div class="spacer"></div>
    <h1 class="headline">Scheduling that<br>doesn't <span class="accent">drift</span></h1>
    <p class="body" style="margin-top: var(--gap); max-width: 80%;">
      Every post now renders from your brand kit, so the blue is your blue.
    </p>
    <div class="spacer"></div>
    <div class="footer">
      <img src="brand/logo/logo.svg" alt="">
      <span class="caption">acme.com</span>
    </div>
  </div>
</body>
</html>
```

```
render_html_image(html="cards/update.html", width=1080, height=1350,
                  scale=2, save_path="renders/update.png")
```

Note the two `.spacer` divs: they push the headline to the optical centre and
pin the footer to the bottom without a single hardcoded offset, so a two-line
headline and a four-line one both sit correctly.

## Photo card with a scrim

The overlay that makes type readable on any photograph. A flat black wash at
50% dims the whole picture; a **scrim gradient** darkens only where the type
actually sits, so the image stays visible everywhere else.

```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="brand/cards.css">
  <style>
    :root { --w: 1080px; --h: 1350px; }
    .card { padding: 0; }
    .photo { position: absolute; inset: 0; }
    .photo img { width: 100%; height: 100%; object-fit: cover; }
    /* Opaque where the text is, clear where it is not. The mid-stop stops the
       gradient banding across the middle of the image. */
    .scrim {
      position: absolute; inset: 0;
      background: linear-gradient(
        to top,
        rgba(11,21,32,0.92) 0%,
        rgba(11,21,32,0.72) 28%,
        rgba(11,21,32,0.15) 52%,
        rgba(11,21,32,0) 70%
      );
    }
    .content {
      position: relative; height: 100%;
      padding: var(--pad);
      display: flex; flex-direction: column; justify-content: flex-end;
      color: #fff;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="photo"><img src="images/hero.png" alt=""></div>
    <div class="scrim"></div>
    <div class="content">
      <h1 class="headline">We shipped it Tuesday.</h1>
      <p class="body" style="margin-top: 24px; opacity: .85;">It broke Wednesday. Here's what changed.</p>
    </div>
  </div>
</body>
</html>
```

`images/hero.png` is whatever `image_generate` just saved — it writes to
`<workspace>/images/`, so a card written at the workspace root reaches it with
exactly this relative path.

## Stat card

One number, large enough to read at thumbnail size, with the context under it.
The most reliably effective social graphic there is, and the one a generative
model gets wrong most often.

```html
<div class="card">
  <p class="caption">Q3 results</p>
  <div class="spacer"></div>
  <div style="font-family: var(--display); font-size: 320px; line-height: .85;
              color: var(--accent);">40%</div>
  <p class="subhead" style="margin-top: var(--gap); max-width: 85%;">
    of signups were lost in the first onboarding step
  </p>
  <div class="spacer"></div>
  <div class="footer">
    <img src="brand/logo/logo.svg" alt="">
    <span class="caption">acme.com</span>
  </div>
</div>
```

## Quote card

```html
<div class="card" style="background: var(--surface);">
  <div class="spacer"></div>
  <div style="font-family: var(--display); font-size: 180px; line-height: .6;
              color: var(--accent); opacity: .35;">&ldquo;</div>
  <p class="subhead" style="margin-top: 8px;">
    The blue is finally our blue.
  </p>
  <p class="caption" style="margin-top: var(--gap);">
    Dana Okoye &middot; Head of Brand, Northwind
  </p>
  <div class="spacer"></div>
  <div class="footer">
    <img src="brand/logo/logo.svg" alt="">
    <span class="caption">acme.com</span>
  </div>
</div>
```

## Carousel

Two outputs from one set of slide bodies.

**Per-slide files → PNG set** (Instagram, TikTok). Write
`slides/slide-01.html` … `slide-08.html`, each a standalone page linking the
shared stylesheet:

```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="../brand/cards.css">
  <style>:root { --w: 1080px; --h: 1350px; }</style>
</head>
<body>
  <div class="card">
    <span class="caption">01 / 08</span>
    <div class="spacer"></div>
    <h1 class="headline">Your posts look<br>generic. Here's why.</h1>
    <div class="spacer"></div>
    <span class="caption accent">Swipe &rarr;</span>
  </div>
</body>
</html>
```

Note the `../` on the stylesheet href — the slide sits one level down. Render
each one, zero-padded so they upload in order:

```
render_html_image(html="slides/slide-01.html", width=1080, height=1350,
                  scale=2, save_path="renders/slide-01.png")
```

Keep the `01 / 08` counter and the swipe cue on slide 1 — completion rate is
what the algorithm reads, and telling people there is more is most of it.

**One document → PDF** (LinkedIn native document post). Concatenate the same
slide bodies into `carousel.html`, with the page break that turns each into its
own PDF page:

```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="brand/cards.css">
  <style>
    :root { --w: 1080px; --h: 1350px; }
    .card { page-break-after: always; break-after: page; }
    .card:last-child { page-break-after: auto; break-after: auto; }
  </style>
</head>
<body>
  <div class="card">…slide 1…</div>
  <div class="card">…slide 2…</div>
  <!-- … -->
</body>
</html>
```

```
render_html_pdf(html="carousel.html", width=1080, height=1350,
                save_path="renders/carousel.pdf")
```

**Check the page count.** A missing `page-break-after` produces a single very
long page that still opens fine in a viewer and is rejected — or renders as one
unreadable slide — on upload. Count the pages before handing it over.

## Story / Reel safe zones

For 1080 × 1920, the platform's own UI covers the top and bottom bands. Reserve
them explicitly rather than eyeballing it:

```html
<style>
  :root { --w: 1080px; --h: 1920px; }
  .card { padding: 250px var(--pad) 400px; justify-content: center; }
</style>
```

While designing, a temporary overlay makes the reserved area visible — delete it
before the final render:

```html
<div style="position:absolute;inset:0;pointer-events:none;
            background:linear-gradient(to bottom,
              rgba(255,0,0,.25) 0 250px, transparent 250px calc(100% - 400px),
              rgba(255,0,0,.25) calc(100% - 400px) 100%);"></div>
```
