# wechat-layout-skill
根据提供的md文件、docx文件、txt文件、md文本，自动生成简洁、精致、好看的公众号排版。生成可【CTRL+C】的HTML 且【CTRL+V】到公众号官方编辑器中。保留样式、格式让你更专注内容，而不用为选择模板而痛苦

## 用法

```bash
# 渲染（默认主题 tech-ai）
python scripts/render.py 文章.md -o 文章.wechat.html

# 切换主题（assets/themes/ 下的目录名，如 growth）
python scripts/render.py 文章.md --theme growth -o 文章.wechat.html

# 校验主题模板是否符合公众号 HTML 规则
python scripts/validate_template.py assets/themes/growth
```

主题 = `assets/themes/<主题名>/` 下的 `theme.json` + `components/*.html`。
新增主题的组件清单与规则见 [references/theme-contract.md](references/theme-contract.md)。

