# Prompting `image_generate`

Worked prompts, one per genre, all in the shape the `image` skill's template uses. Copy the closest one, swap the nouns, keep the negatives.

## The template

```
Subject:      one main subject, its state and action
Style:        photograph / flat illustration / watercolor / 3D render / cartoon …
Composition:  framing, angle, where the empty space goes
Lighting:     direction, quality, colour of the light
Palette:      3–4 colour words (brand colours by name when brand/tokens.json exists)
Mood:         two or three adjectives
Negatives:    no text, no words, no lettering, no logos, no watermark, plus genre-specific ones
```

Say it as prose, 40–90 words. The order above is also the order of importance: if the model has to drop something, it drops the end. Always pass an `aspect_ratio` (`1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `21:9`), `quality: "high"` for deliverables, `n: 1`.

## 1. Photograph — blog hero (workspace scene)

```
image_generate(
  prompt="A clean oak desk seen from slightly above with a closed laptop, a ceramic mug and a paper notebook, editorial photograph, 35mm lens, shallow depth of field, soft morning window light from the left, palette of warm oak, off-white and slate blue, calm and focused mood, generous empty space across the upper half. No text, no words, no lettering, no logos, no screens showing content, no people.",
  aspect_ratio="16:9", quality="high")
```

Why it works: a real surface, a lens, a light direction, and the empty space named — the headline will be rendered over the upper half.

## 2. Photograph — product lifestyle (blank screen for a real screenshot)

```
image_generate(
  prompt="A person's hands holding a modern smartphone with a completely blank dark screen, in a bright café, medium close-up, 85mm portrait lens, shallow depth of field, natural daylight from a window behind, palette of warm neutrals with a teal accent from a mug, candid and unposed mood. The screen is plain dark glass with nothing on it. No text, no UI, no icons, no logos, no watermark.",
  aspect_ratio="3:4", quality="high")
```

Then the real screenshot goes over the screen area in HTML (`object-fit: cover`, a slight `transform: perspective(...)` if the phone is angled) and `render_html_image` produces the mockup at 1080×1350.

## 3. Illustration — flat vector editorial

```
image_generate(
  prompt="A small rowing boat crossing a calm lake toward a lighthouse, flat vector illustration, clean 2px linework, simple geometric shapes, four-colour palette of navy, mustard, cream and coral, subtle paper-grain texture, mid-century travel-poster feel, wide composition with the boat in the lower-left third and open sky above, optimistic and quiet mood. No text, no words, no lettering, no logos, no gradients, no photorealism.",
  aspect_ratio="16:9", quality="high")
```

Why it works: medium (`flat vector`), line weight, a named palette and an era instead of an artist's name.

## 4. Illustration — watercolor

```
image_generate(
  prompt="A single potted monstera on a windowsill, loose watercolor illustration on cold-pressed paper, visible brush edges and soft colour bleeds, palette of sage green, ochre and pale grey wash, white paper left showing around the subject, centred composition with wide margins, gentle and unhurried mood. No text, no words, no lettering, no logos, no outlines in black ink, no digital sharpness.",
  aspect_ratio="1:1", quality="high")
```

## 5. Cartoon / character — with a character sheet

Write the sheet once and paste it verbatim into every prompt for that character:

```
CHARACTER SHEET: Pip, a small round robot the size of a kettle, matte cream body with a single teal LED eye,
short stubby arms, tank-tread feet, a tiny brass antenna with a red tip, always carries a green watering can.
```

```
image_generate(
  prompt="CHARACTER SHEET: Pip, a small round robot the size of a kettle, matte cream body with a single teal LED eye, short stubby arms, tank-tread feet, a tiny brass antenna with a red tip, always carries a green watering can. SCENE: Pip waters a row of sunflowers in a garden, cheerful cartoon illustration, bold clean outlines, flat cel shading, palette of cream, teal, sunflower yellow and leaf green, medium shot at Pip's eye level, sunny and friendly mood. No text, no words, no lettering, no logos, no extra limbs, no extra eyes, no other robots.",
  aspect_ratio="4:3", quality="high")
```

For the next image change only the SCENE sentence. The negatives `no extra limbs, no extra eyes, no other robots` guard the sheet.

## 6. 3D icon

```
image_generate(
  prompt="A single padlock as a 3D app icon, glossy soft-touch plastic with a brushed brass shackle, rounded edges, isometric three-quarter view, soft studio lighting with a gentle top-left key light and subtle ambient occlusion, centred on a plain deep-navy background with generous margin on every side, palette of navy, brass and off-white, clean and trustworthy mood. No text, no words, no lettering, no logos, no reflections of other objects, no floor grid.",
  aspect_ratio="1:1", quality="high")
```

Material words (`soft-touch plastic`, `brushed brass`) plus render words (`ambient occlusion`, `key light`) are what make it read as an icon rather than a photo.

## 7. Abstract background — artwork layer for a social graphic

```
image_generate(
  prompt="Abstract background of slow flowing gradients and a few soft translucent geometric shapes, deep navy fading to warm grey with one coral highlight in the upper-right corner, smooth and matte, no sharp detail anywhere, the lower two-thirds almost uniform and dark so overlaid text stays readable, modern and calm mood. No text, no words, no lettering, no logos, no people, no objects, no watermark.",
  aspect_ratio="9:16", quality="high")
```

Why it works: it asks for a *background*, says where the quiet area is, and keeps the palette to the brand's three colour words. The headline, stat and logo are HTML on top.

## 8. Wide banner backdrop

```
image_generate(
  prompt="Panoramic view of rolling dunes at dawn photographed with a long lens, low sun from the right, thin mist in the valleys, palette of sand, dusty rose and pale blue, the right half of the frame open sky and nearly empty, serene and spacious mood, photorealistic editorial photograph. No text, no words, no lettering, no logos, no people, no vehicles, no watermark.",
  aspect_ratio="21:9", quality="high")
```

Crop to 1584×396 or 1500×500 when composing; the empty right half is where the tagline and logo go.

## 9. Isometric tech scene

```
image_generate(
  prompt="A small isometric city block of stylised server buildings connected by glowing lines, clean 3D render with matte surfaces, soft even studio lighting, palette of graphite, electric blue and white, floating on a plain white background with wide margins, precise and modern mood. No text, no words, no lettering, no logos, no screens, no icons, no watermark.",
  aspect_ratio="4:3", quality="high")
```

## 10. Editorial portrait — illustration, no real person

```
image_generate(
  prompt="A portrait of an imagined middle-aged scientist in a lab coat, painterly digital illustration with visible brush strokes, three-quarter view looking slightly off camera, dramatic single-source side light, palette of teal, amber and deep charcoal, thoughtful and dignified mood, plain dark background with space above the head. No text, no words, no lettering, no logos, no name badge, no glasses reflections, no extra hands.",
  aspect_ratio="3:4", quality="high")
```

Portraits of real people are not a generation task — use their photograph. Imagined people are fine; `no name badge` keeps the model from inventing a label.

## Fixing with one `image_edit`

When QA finds one wrong region, mask it and describe only the replacement:

```
image_edit(image="images/oak-desk-...-1.png", mask="images/oak-desk-mask.png",
           prompt="Replace the object in the masked area with a plain ceramic mug in off-white matching the scene's soft morning light. No text, no logos.")
```

The mask is a PNG the size of the image, transparent where the change goes. One pass; if it is still wrong, change the original prompt instead of stacking edits.
