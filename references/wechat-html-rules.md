# WeChat Official Account HTML Rules

This project renders HTML fragments for the WeChat Official Account editor.
Templates and generated output should follow these rules.

## Required

- Put all styles in inline `style` attributes. WeChat strips `<style>` and external CSS.
- Use `<section>` for block containers. It is more stable in WeChat than `<div>`.
- Render headings with `<p>` plus inline `font-size` and `font-weight:bold`; avoid `<h1>` to `<h6>`.
- Use solid `background-color`; avoid `linear-gradient`.
- Keep `border-radius` between `6px` and `8px` for cards.
- Use `margin` and `padding` with `px` units.
- Body font stack: `-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif`.
- Code font stack: `Menlo,Consolas,monospace`.
- Escape HTML special characters in user content and code blocks.

## Forbidden

- Do not use `display:flex` or `display:grid`.
- Do not use `<div>` as a primary container.
- Do not use `<h1>` to `<h6>`.
- Do not use `<table>` for complex layout. Simple data tables are allowed only when every style is inline.
- Do not use `position:absolute` or `position:fixed`.
- Do not use `float` layout.
- Do not rely on external image URLs. Images should be uploaded to the WeChat media library.
- Do not use `<script>`, `<link>`, or `<style>`.
- Do not use `@media`.
- Do not rely on `class` or `id` selectors.

## Validation Scope

The first implementation validates the obvious high-risk tags, attributes, and CSS properties.
More WeChat-specific edge cases can be added to `scripts/wechat_rules.py` as they are discovered.
