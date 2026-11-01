# 主题组件契约

主题 = 一个目录：`assets/themes/<主题名>/theme.json` + `components/*.html`。
渲染器（`scripts/renderer.py`）与主题之间的接口就是本文的组件清单：
**所有主题的组件文件名集合相同，内容（HTML/样式）各自独立**。

## 新增主题三步法

1. 复制任一现有主题目录为新名字（如 `assets/themes/growth/`），改掉 `theme.json` 的 `name`。
2. 按下面清单修改各组件的 HTML 与样式。
3. 跑 `python scripts/validate_template.py assets/themes/<主题名>/` 校验合规，再跑
   `python scripts/render.py 样例.md --theme <主题名>` 看效果。

## 必需组件（17 个）

缺任何一个 `load_theme` 都会报错并列出缺失文件名。

| 组件 | 变量 | 说明 |
| --- | --- | --- |
| `article` | `$content` | 文章外层容器，控制正文字体/字号/行高/留白 |
| `heading-h1` | `$content` | 一级标题 |
| `heading-h2` | `$content`、`$part_number` | 二级标题，`$part_number` 为按出现顺序的章节号（纯数字） |
| `heading-h3` | `$content` | 三级标题（H4-H6 复用此模板） |
| `paragraph` | `$content` | 普通段落 |
| `quote` | `$content` | 引用块 |
| `code` | `$content`、`$lang` | 代码块，内容已转义 |
| `list` | `$items` | 列表容器，`$items` 为渲染器拼好的列表项 |
| `list-item-ul` | `$content` | 无序列表项（圆点等符号直接写在模板里） |
| `list-item-ol` | `$content`、`$number` | 有序列表项，`$number` 为按起始编号连续生成的纯数字 |
| `card` | `$title`、`$content` | 通用信息卡片（:::card/tip/example/pros/cons/note 共用） |
| `highlight` | `$content` | 强调卡片（:::highlight，无标题） |
| `warning` | `$title`、`$content` | 警告卡片（:::warning） |
| `divider` | 无 | 分割线 |
| `image_placeholder` | 无 | 图片占位 |
| `inline-code` | `$content` | 行内代码的 span 包装（内容已转义） |
| `strong` | `$content` | 加粗的 strong 包装 |

`divider`、`image_placeholder`、`inline-code`、`strong` 四个组件必须**单行、不带注释**：
它们被替换进文本节点中间，多行内容会被拆行或参与注释剥离。

## 通用变量（自动注入，任何模板都能用）

| 变量 | 来源 | 缺省值 |
| --- | --- | --- |
| `$primary` | theme.json `primary` | `#4F46E5` |
| `$light_bg` | theme.json `light_bg` | `#F0F4FF` |
| `$body_color` | theme.json `body_color` | `#333333` |
| `$body_font_size` | theme.json `body_font_size` | `15px` |
| `$body_line_height` | theme.json `body_line_height` | `1.9` |

配色方案参考 `references/layout-parameters.md`。

## 模板书写规则

占位符语法仅限 `string.Template`：`$var` 或 `${var}`，不支持逻辑（if/for）。

- **注释里不要出现 `$变量` 写法**：模板引擎不认识 HTML 注释，注释里的 `$content`
  也会被替换，替换值含另一层注释时会破坏注释剥离、在产物里泄漏 `-->`。
- 渲染器在渲染完成后会统一剥掉模板注释（替换为换行），所以块级模板可以放心写注释；
  但上面列出的 4 个行内/无变量组件除外。
- HTML 合规红线（公众号编辑器限制）见 `references/wechat-html-rules.md`：
  `<section>` 做容器、全内联样式、禁 flex/grid/position/float/渐变/@media/`<h1>`-`<h6>`。
- `theme.json` 只放"参数级"差异（颜色、字号、行高）；"结构级"差异（有没有装饰线、
  胶囊还是章节号）放各自的 HTML 模板。
