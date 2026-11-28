---
name: design-github-readme-heroes
description: Create, redesign, or audit the lead figure in a GitHub repository's root README. Use for project covers, architecture heroes, visual abstracts, and README banners that need a distinctive project identity, an accurate first-glance explanation, and legible desktop and phone layouts. Also use when a user supplies a reference cover and wants its visual quality carried across projects.
---

# Design GitHub README heroes

**English** · [简体中文](SKILL.zh-CN.md)

Give a first-time reader one question, one visual answer and a way to verify it.

## Decide what earns the first screen

1. Open the actual root README and its referenced asset. Read the smallest set of project materials that can support the visual claim, such as a contract, recorded run, evaluation, sample output or design specification. For a redesign, preview the current lead image at README width.
2. Write a one-sentence brief naming the audience, the distinctive mechanism, the observed result and its scope. Identify which parts are proposed, simulated, deployed or measured. Use the project's public name and requested attribution. A concept can have an excellent cover grounded in a clearly labeled design question.
3. Inspect any reference at its target width. Extract its reading order, focal point, spacing, color roles, typography and domain-specific marks. Create original geometry and wording for the current project. Keep private references and identifying assets out of public deliverables unless authorized.

## Compose the figure

- Put the project identity and a short, concrete question or finding where the eye lands first. Give the mechanism that distinguishes the project the largest or most visually prominent region.
- Choose a composition that follows the evidence. A process can use a journey, a threshold a calibrated scale, a dataset a real specimen, and an empirical result a comparison with units. See [layout recipes](references/layout-recipes.md).
- Design one memorable domain-specific mark. Use a restrained field, a clear baseline grid, consistent type and a few accents with distinct meanings. Repeat each color's meaning with words or shape. Give labels and connectors separate space. A dark layered field with mint, violet and amber is a useful starting point for a technical cover when it fits the project.
- Draw a small color study before detailing the figure. Reserve the deepest value for the field, lift the important mechanism by one value step, and spend the highest saturation on the few marks that carry the claim. Translate one real project object into original line art with an outer silhouette and two or three meaningful interior details. Use directional light, a shaded face, or an engraved detail to give it volume. Keep glows and patterns away from small type.
- Use direct labels and ordinary language. Move long identifiers, detailed branches, credits and instructions into nearby Markdown. Use a status label only if readers could otherwise mistake the maturity or provenance of the work. Finish with a concrete outcome or verification detail.
- Compose for the rendered width. Start with a roughly 2:1 landscape canvas and inspect it in a README-sized column. Aim for readable text around 14–18 CSS pixels or larger at the intended width. Recompose a dense landscape as a narrow figure with stacked or simplified content. Preserve the headline, mechanism, result and evidence caveat at both sizes.

## Produce and embed

1. For exact labels, data and connectors, author editable native SVG with a viewBox, intrinsic dimensions, embedded styles, meaningful title and description, local fragment references and system font fallbacks. Use a deterministic generator when two layouts share measurements or change together. If the hero includes illustration, keep exact text and data in the editable vector layer. Record the actual tools and source evidence with the project.
2. Place the hero immediately below the project heading, and keep the existing technical diagram accessible from the relevant section. Use a concise, specific alt and a normal Markdown link to the proof. Use the README's audience language for the alt or adjacent text.
3. When the narrow composition differs, use a GitHub-supported picture element with the narrow source first and the wide image as fallback. Adjust the breakpoint to the point at which the *content* becomes illegible. Include a direct narrow-view link when the hosting surface discards responsive sources. PNG exports are useful for slide, social or static-preview consumers.

```html
<picture>
  <source media="(max-width: 720px)" srcset="docs/hero-mobile.svg">
  <img src="docs/hero.svg" width="100%" alt="Describe the project's mechanism and its result.">
</picture>
```

## Verify before delivery

- Run the bundled checker with Python 3, Playwright and Chromium. For example, `python scripts/check_hero.py docs/hero.svg --mobile docs/hero-mobile.svg --out /tmp/hero-review`. Use `--browser` for a system Chromium build, `--breakpoint` to match the README, and `--export-wide cover.png` for a standalone PNG. It checks self-contained SVGs, renders the responsive image, exercises both page themes, and reports off-canvas text, undersized labels and likely overlaps.
- Open the generated previews. Trace every connector. Check label contrast on its actual surface, verify alignment, and read the image at normal size without zooming. Squint at a thumbnail and inspect a grayscale copy. The focal object and evidence should still read in the intended order. If a measured label is intentionally small, increase its size or move its meaning into the adjacent prose. Follow the proof link and compare each number, unit, branch and status to the underlying evidence.
- Check the host's rendered README when accessible, including source selection on a phone and a working image fallback. If only local verification was possible, say exactly what was tested. Deliver the real figure, its editable source and where readers can find it in the README.
