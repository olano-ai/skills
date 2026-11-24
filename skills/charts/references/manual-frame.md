# Manual frame — the copy-paste template

For an agent without a shell: fill in the two placeholders, save the file with
`write_file` (for example to `reports/<name>.html`) and render it with
`render_html_image(html="reports/<name>.html", width=1200, height=1200,
save_path="reports/<name>.png", wait_for=".render-done")`.

- `__SKILL_DIR__` → this skill's absolute directory (shown where the skill was loaded),
  so the three `<script src>` lines point at `assets/vendor/*.min.js`.
- `__SPEC__` → a Vega-Lite spec (a recipe's `--emit-vl` output, or one written from the
  cookbook). Leave `width`/`height` out; the page sizes it to the box.

The template uses the `clean` theme; the `midnight` values are in the comment. It falls
back to the system sans-serif (the script embeds the bundled fonts as data URIs — a
`file://` font is often blocked by the browser's font policy, so a manual page should not
depend on one).

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Chart</title>
<style>
  :root {
    /* clean */
    --surface: #fcfcfb; --ink: #0b0b0b; --secondary: #52514e; --muted: #898781;
    --grid: #e1e0d9; --baseline: #c3c2b7; --accent: #2a78d6; --deemphasis: #c9c8c1;
    /* midnight: --surface:#0d0d0d; --ink:#ffffff; --secondary:#c3c2b7; --muted:#8b8a84;
       --grid:#2c2c2a; --baseline:#383835; --accent:#c98500; --deemphasis:#3a3a38; */
    --font: system-ui, -apple-system, "Segoe UI", sans-serif;
  }
  html, body { margin: 0; background: var(--surface); }
  #frame { width: 1200px; height: 1200px; box-sizing: border-box; padding: 72px;
           display: flex; flex-direction: column; background: var(--surface);
           color: var(--ink); font-family: var(--font); overflow: hidden; }
  .kicker { font-size: 16px; font-weight: 700; letter-spacing: .14em; text-transform: uppercase;
            color: var(--secondary); margin: 0 0 14px; }
  h1 { font-size: 50px; line-height: 1.08; font-weight: 700; letter-spacing: -.015em; margin: 0 0 12px; }
  .subtitle { font-size: 24px; line-height: 1.3; color: var(--secondary); margin: 0 0 28px; }
  #chart { flex: 1; min-height: 0; }
  #chart .vega-embed { width: 100%; height: 100%; }
  #chart .vega-embed summary, #chart .vega-embed details { display: none; }
  .footer { display: flex; justify-content: space-between; gap: 24px; margin-top: 28px;
            font-size: 15px; color: var(--muted); }
</style>
</head>
<body>
<div id="frame">
  <p class="kicker">Customer footprint</p>
  <h1>The US is a third of the customer base</h1>
  <p class="subtitle">Accounts by billing country · 63 total</p>
  <div id="chart"></div>
  <div class="footer"><span>Source: Salesforce · as of 2026-09-06</span><span>3 accounts have no billing country and are not shown.</span></div>
</div>
<script src="file://__SKILL_DIR__/assets/vendor/vega.min.js"></script>
<script src="file://__SKILL_DIR__/assets/vendor/vega-lite.min.js"></script>
<script src="file://__SKILL_DIR__/assets/vendor/vega-embed.min.js"></script>
<script>
  var spec = __SPEC__;
  var css = getComputedStyle(document.documentElement);
  var t = function (name) { return css.getPropertyValue(name).trim(); };
  spec.$schema = spec.$schema || "https://vega.github.io/schema/vega-lite/v6.json";
  spec.config = Object.assign({
    background: t("--surface"), font: t("--font"), padding: 0,
    view: { stroke: null },
    axis: { domain: false, ticks: false, grid: false, gridColor: t("--grid"), gridWidth: 1,
            domainColor: t("--baseline"), labelColor: t("--muted"), labelFontSize: 18,
            titleColor: t("--secondary"), titleFontSize: 18, titleFontWeight: 400, labelPadding: 10 },
    legend: { orient: "top", direction: "horizontal", title: null, symbolType: "circle",
              labelColor: t("--secondary"), labelFontSize: 18, symbolSize: 120 },
    bar: { cornerRadiusEnd: 4 }, line: { strokeWidth: 2, strokeJoin: "round", strokeCap: "round" },
    point: { filled: true, stroke: t("--surface"), strokeWidth: 2 },
    text: { color: t("--ink"), fontSize: 19, fontWeight: 700 },
    range: { category: ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"] }
  }, spec.config || {});
  var box = document.getElementById("chart").getBoundingClientRect();
  if (spec.mark || spec.layer) {           // single or layered views fit the box exactly
    spec.width = Math.round(box.width); spec.height = Math.round(box.height);
    spec.autosize = { type: "fit", contains: "padding" };
  }
  function done(err) {
    var d = document.createElement("div");
    d.className = "render-done" + (err ? " render-failed" : "");
    d.hidden = true; if (err) d.setAttribute("data-error", String(err));
    document.body.appendChild(d);
  }
  (document.fonts ? document.fonts.ready : Promise.resolve())
    .then(function () { return vegaEmbed("#chart", spec, { renderer: "svg", actions: false }); })
    .then(function () { done(null); })
    .catch(function (err) {
      document.getElementById("chart").textContent = "Chart failed to render: " + (err && err.message || err);
      done(err);
    });
</script>
</body>
</html>
```

For a `midnight` card swap the variable block and the category range for the dark values
(`#3987e5 #d95926 #199e70 #c98500 #d55181 #008300 #9085e9 #e66767`). For another preset
change `#frame`'s width/height and padding (see `marks-and-anatomy.md`) and pass the same
numbers to `render_html_image`. Keep the `.render-done` sentinel: it is what the renderer
waits for.
