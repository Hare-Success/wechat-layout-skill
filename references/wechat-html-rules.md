# 微信公众号 HTML 规则

本项目为公众号编辑器渲染 HTML 片段，模板与生成结果都应遵循以下规则。

## 必须遵循

- 所有样式写在行内 `style` 属性中，公众号会剥离 `<style>` 和外部 CSS。
- 块级容器使用 `<section>`，在公众号中比 `<div>` 更稳定。
- 标题用 `<p>` 加行内 `font-size` 和 `font-weight:bold` 渲染，避免 `<h1>` 到 `<h6>`。
- 使用纯色 `background-color`，避免 `linear-gradient`。
- 卡片的 `border-radius` 保持在 6px 到 8px。
- `margin` 和 `padding` 使用 `px` 单位。
- 正文字体栈：`-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif`。
- 代码字体栈：`Menlo,Consolas,monospace`。
- 用户内容与代码块中的 HTML 特殊字符必须转义。

## 禁止使用

- 不要使用 `display:flex` 或 `display:grid`。
- 不要用 `<div>` 作为主要容器。
- 不要使用 `<h1>` 到 `<h6>`。
- 不要用 `<table>` 做复杂布局；简单数据表格仅在所有样式均为行内时可用。
- 不要使用 `position:absolute` 或 `position:fixed`。
- 不要使用 `float` 布局。
- 不要依赖外部图片 URL，图片应上传到公众号素材库。
- 不要使用 `<script>`、`<link>` 或 `<style>`。
- 不要使用 `@media`。
- 不要依赖 `class` 或 `id` 选择器。

## 校验范围

当前实现校验显而易见的高风险标签、属性和 CSS 属性。后续发现的公众号特有边界情况，可继续补充到 `scripts/wechat_rules.py`。
