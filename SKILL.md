---
name: wechat-layout
description: "微信公众号文章排版技能。Use when the user asks to 排版/生成公众号文章、微信推文、公众号 HTML，要把 Markdown/文本转成可粘贴到微信公众号编辑器的格式，或要调整公众号文章的主题样式。Triggers: 公众号排版、公众号文章、微信推文、WeChat Official Account article."
---

# WeChat Layout

把 Markdown 渲染成微信公众号可用的内联样式 HTML：全选复制产物，直接粘贴进公众号编辑器即保留排版。
下述路径均相对本 skill 根目录。

## 工作流

### 1. 输入处理（统一整理成 Markdown）
- `.md`：直接使用。
- `.txt` 或对话中粘贴的文本：整理成规范 Markdown（补标题层级 `#`、列表、代码块围栏），再进入渲染。
- `.docx`：解析器只支持 Markdown，先转换（pandoc 或读取后转写），再渲染。

### 2. 选择主题（--theme）
主题 = `assets/themes/<主题名>.html` 单文件。按以下优先级确定：
1. **用户点名**主题名 → 直接使用；
2. **用户描述风格**（颜色/行业/调性）→ 运行 `ls assets/themes/*.html` 并读每个文件头部
   注释与 `@config` 的 `display_name`/`description`，匹配最接近的；配色方向参考
   `references/layout-parameters.md`；
3. **未提及** → 默认 `tech-ai`，交付时附一句现有主题清单供用户替换。

### 3. 渲染
```bash
python scripts/render.py 文章.md --theme <主题名> -o 文章.wechat.html
```
- 校验默认开启且**不要用 `--no-validate` 绕过**（除非用户明确要求并自担风险）。
- 需要排查解析问题时可加 `--ast 输出.json` 查看 AST。

### 4. 交付
- 产物是 HTML **片段**：告知用户用编辑器打开、全选复制、粘贴进公众号编辑器。
- 图片渲染为灰色占位块，用户需在公众号编辑器中上传替换（不依赖外部图链）。

## 样式调整与新增主题
- 改样式：打开 `assets/themes/<主题名>.html`，找到对应 `@component` 段直接改 HTML/内联样式，改完重渲染。
- 新增主题：复制任一主题 `.html` 文件改名，按 `references/theme-contract.md` 的组件契约修改；
  用 `python scripts/validate_template.py assets/themes/<主题名>.html` 校验。

## 故障处理
- 渲染抛 `ValueError`（违反公众号规则）：把违规明细逐条转述给用户，先改内容或模板，**不要**绕过校验。
- 报"缺少必需组件"：对照 `references/theme-contract.md` 在主题文件里补齐 `@component` 段。
- 报"主题不存在"：`ls assets/themes/` 列出可用主题给用户选。

## 已知限制
- 块内不支持嵌套（卡片/引用里不能放列表或代码块）。
- `[链接](url)` 与 `![]()` 不渲染为链接/图片，图片语法按占位块处理。
- 公众号正文不支持超链接与 `<h1>-<h6>`，标题已用 `<p>` 模拟，属预期行为。

## 参考文档（按需读取）
| 场景 | 文档 |
| --- | --- |
| 改主题/加主题、组件契约 | `references/theme-contract.md` |
| 排查"违反公众号规则"报错 | `references/wechat-html-rules.md` |
| 选主题、调字号间距配色 | `references/layout-parameters.md` |
