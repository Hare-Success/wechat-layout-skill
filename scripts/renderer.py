"""AST + 主题模板 → 微信公众号内联 HTML 渲染器。

流水线的第二步：把 parser 产出的 Block 列表套用主题组件模板，
生成全内联样式的 HTML（公众号编辑器不支持 <style> 和 class），
最后经 wechat_rules 校验后输出。

渲染器只负责语义：块类型 → 组件模板名的分发、标题层级映射、
列表编号、卡片默认标题，以及 HTML 转义与行内标记的替换顺序。
全部视觉样式（含标题、列表项、行内代码、加粗的外观）都来自
主题的 components/*.html，换主题 = 换目录，渲染器零改动。
"""

from __future__ import annotations

import html
import re
from scripts.parser import Block
from scripts.parser import unescape_markdown_text
from scripts.theme_loader import Theme
from scripts.wechat_rules import validate_html


# 主题缺省值：theme.json 未配置时使用
PRIMARY = "#4F46E5"
LIGHT_BG = "#F0F4FF"
BODY_COLOR = "#333333"
BODY_FONT_SIZE = "15px"
BODY_LINE_HEIGHT = "1.9"


def render(blocks: list[Block], theme: Theme, validate: bool = True) -> str:
    """渲染整个文档：逐块渲染后包进 article 模板，可选执行公众号规则校验。

    Args:
        blocks: parser 解析出的 Block 列表。
        theme: 已加载的主题。
        validate: 是否对产物执行公众号规则校验，违规时抛 ValueError。

    Returns:
        可直接粘贴进公众号编辑器的内联样式 HTML。
    """
    rendered_blocks: list[str] = []
    section_number = 0
    for block in blocks:
        # 二级标题按出现顺序编号，供 heading-h2 模板渲染章节号
        if block.type == "heading" and block.level == 2:
            section_number += 1
            rendered_blocks.append(render_block(block, theme, section_number=section_number))
        else:
            rendered_blocks.append(render_block(block, theme))
    body = "\n".join(item for item in rendered_blocks if item.strip())
    html_output = _template(theme, "article", content=body)
    # 公众号会保留 HTML 注释，渲染完成后统一剥掉模板里的注释
    html_output = _strip_html_comments(html_output)

    if validate:
        violations = validate_html(html_output)
        if violations:
            details = "\n".join(f"- {item.rule}: {item.detail}" for item in violations)
            raise ValueError(f"生成的 HTML 违反公众号规则：\n{details}")

    return html_output


def render_block(block: Block, theme: Theme, section_number: int | None = None) -> str:
    """按 Block 类型分发到对应的组件模板，渲染单个块的 HTML。"""
    if block.type == "heading":
        return _render_heading(block, theme, section_number)
    if block.type == "paragraph":
        return _template(theme, "paragraph", content=_inline(block.content, theme))
    if block.type == "quote":
        return _template(theme, "quote", content=_inline_multiline(block.content, theme))
    if block.type == "code":
        return _template(theme, "code", content=html.escape(unescape_markdown_text(block.content)), lang=html.escape(block.lang or "text"))
    if block.type == "unordered_list":
        items = "\n".join(_unordered_list_item(theme, item) for item in block.items)
        return _template(theme, "list", items=items)
    if block.type == "ordered_list":
        start = int(block.meta.get("start", 1))
        items = "\n".join(
            _ordered_list_item(theme, str(start + index), item)
            for index, item in enumerate(block.items)
        )
        return _template(theme, "list", items=items)
    if block.type == "card":
        kind = block.meta.get("kind", "card")
        title = block.title or _default_card_title(kind)
        # highlight 无标题、warning 有专属模板，其余卡片共用 card 模板
        if kind == "highlight":
            return _template(theme, "highlight", content=_inline_multiline(block.content, theme))
        if kind == "warning":
            return _template(theme, "warning", title=_inline(title, theme), content=_inline_multiline(block.content, theme))
        return _template(theme, "card", title=_inline(title, theme), content=_inline_multiline(block.content, theme))
    if block.type == "image_placeholder":
        return _template(theme, "image_placeholder")
    if block.type == "divider":
        return _template(theme, "divider")
    # 未知类型兜底按段落渲染，避免直接报错中断
    return _template(theme, "paragraph", content=_inline(block.content, theme))


def _template(theme: Theme, name: str, **values: str) -> str:
    """取组件模板并做变量替换，自动注入主题配色与正文的缺省值。

    任何模板都可以直接引用 $primary / $light_bg / $body_color /
    $body_font_size / $body_line_height，无需渲染器逐个传参。
    """
    defaults = {
        "primary": theme.config.get("primary", PRIMARY),
        "light_bg": theme.config.get("light_bg", LIGHT_BG),
        "body_color": theme.config.get("body_color", BODY_COLOR),
        "body_font_size": theme.config.get("body_font_size", BODY_FONT_SIZE),
        "body_line_height": theme.config.get("body_line_height", BODY_LINE_HEIGHT),
    }
    defaults.update(values)
    return theme.component(name).safe_substitute(defaults)


def _render_heading(block: Block, theme: Theme, section_number: int | None) -> str:
    """渲染标题：按级别选模板，H4-H6 复用 H3（公众号正文里太深的层级没有区分意义）。

    三级标题的全部外观由主题的 heading-h1/h2/h3 模板决定，
    渲染器只传内容与 H2 的章节编号。
    """
    level = min(max(block.level or 1, 1), 3)
    if level == 1:
        return _template(theme, "heading-h1", content=_inline(block.content, theme))
    if level == 2:
        # section_number 在 render() 中按 H2 出现顺序递增，正常必有值
        part_number = str(section_number) if section_number is not None else ""
        return _template(theme, "heading-h2", content=_inline(block.content, theme), part_number=part_number)
    return _template(theme, "heading-h3", content=_inline(block.content, theme))


def _unordered_list_item(theme: Theme, content: str) -> str:
    """渲染单个无序列表项，圆点符号与样式由主题的 list-item-ul 模板决定。"""
    return _template(theme, "list-item-ul", content=_inline(content, theme))


def _ordered_list_item(theme: Theme, number: str, content: str) -> str:
    """渲染单个有序列表项，编号样式由主题的 list-item-ol 模板决定。"""
    return _template(theme, "list-item-ol", content=_inline(content, theme), number=number)


def _inline(text: str, theme: Theme) -> str:
    """处理行内样式：先转义 HTML，再按固定顺序替换行内标记。

    替换顺序有讲究：先 `` 行内代码，再 ** / __ 加粗，最后 <u> / ++ 下划线。
    行内代码最先替换，保证代码内容里的 ** 等记号不再被后续规则二次处理。
    行内代码与加粗的外观由主题的 inline-code / strong 模板提供。
    """
    escaped = html.escape(unescape_markdown_text(text.strip()))
    # 行内代码 `code`
    escaped = re.sub(
        r"`([^`]+)`",
        lambda match: _template(theme, "inline-code", content=match.group(1)),
        escaped,
    )
    # 加粗 **text**
    escaped = re.sub(
        r"\*\*(.+?)\*\*",
        lambda match: _template(theme, "strong", content=match.group(1)),
        escaped,
    )
    # 加粗 __text__
    escaped = re.sub(
        r"__(.+?)__",
        lambda match: _template(theme, "strong", content=match.group(1)),
        escaped,
    )
    # 下划线：<u>text</u>（原文里的 <u> 已被转义，所以匹配转义后的形式）
    escaped = re.sub(
        r"&lt;u&gt;(.+?)&lt;/u&gt;",
        lambda match: f'<span style="text-decoration:underline;text-underline-offset:3px;">{match.group(1)}</span>',
        escaped,
    )
    # 下划线：++text++
    escaped = re.sub(
        r"\+\+(.+?)\+\+",
        lambda match: f'<span style="text-decoration:underline;text-underline-offset:3px;">{match.group(1)}</span>',
        escaped,
    )
    return escaped


def _strip_html_comments(html_text: str) -> str:
    """删除 HTML 注释，替换为单个换行（避免相邻标签粘连）。"""
    return re.sub(r"\s*<!--.*?-->\s*", "\n", html_text, flags=re.DOTALL)


def _inline_multiline(text: str, theme: Theme) -> str:
    """对多行文本逐行做行内替换，行间用 <br> 连接（引用、卡片正文用）。"""
    lines = [_inline(line, theme) for line in text.splitlines() if line.strip()]
    return "<br>".join(lines)


def _default_card_title(kind: str) -> str:
    """卡片未显式指定标题时的默认标题。"""
    return {
        "note": "Note",
        "warning": "Warning",
        "tip": "提示",
        "example": "示例",
        "pros": "正例",
        "cons": "反例",
    }.get(kind, "重点")
