from __future__ import annotations

import html
import re
from scripts.parser import Block
from scripts.parser import unescape_markdown_text
from scripts.theme_loader import Theme
from scripts.wechat_rules import validate_html


PRIMARY = "#4F46E5"
LIGHT_BG = "#F0F4FF"


def render(blocks: list[Block], theme: Theme, validate: bool = True) -> str:
    rendered_blocks: list[str] = []
    section_number = 0
    for block in blocks:
        if block.type == "heading" and block.level == 2:
            section_number += 1
            rendered_blocks.append(render_block(block, theme, section_number=section_number))
        else:
            rendered_blocks.append(render_block(block, theme))
    body = "\n".join(item for item in rendered_blocks if item.strip())
    html_output = theme.component("article").safe_substitute(
        content=body,
        primary=theme.config.get("primary", PRIMARY),
        light_bg=theme.config.get("light_bg", LIGHT_BG),
    )
    html_output = _strip_html_comments(html_output)

    if validate:
        violations = validate_html(html_output)
        if violations:
            details = "\n".join(f"- {item.rule}: {item.detail}" for item in violations)
            raise ValueError(f"Generated HTML violates WeChat rules:\n{details}")

    return html_output


def render_block(block: Block, theme: Theme, section_number: int | None = None) -> str:
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
        component = "highlight" if kind == "highlight" else "card"
        return _template(theme, component, title=_inline(title, theme), content=_inline_multiline(block.content, theme))
    if block.type == "image_placeholder":
        return _template(theme, "image_placeholder")
    if block.type == "divider":
        return _template(theme, "divider")
    return _template(theme, "paragraph", content=_inline(block.content, theme))


def _template(theme: Theme, name: str, **values: str) -> str:
    defaults = {
        "primary": theme.config.get("primary", PRIMARY),
        "light_bg": theme.config.get("light_bg", LIGHT_BG),
    }
    defaults.update(values)
    return theme.component(name).safe_substitute(defaults)


def _render_heading(block: Block, theme: Theme, section_number: int | None) -> str:
    level = min(max(block.level or 1, 1), 3)
    primary = theme.config.get("primary", PRIMARY)

    if level == 1:
        return _template(
            theme,
            "heading",
            section_style="text-align:center;padding:25px 0 15px 0;",
            part_block="",
            title_style="font-size:23px;font-weight:bold;color:#1a1a1a;line-height:1.5;margin:0;",
            content=_inline(block.content, theme),
            title_decoration=f'<section style="width:40px;height:3px;background-color:{primary};margin:14px auto 0 auto;border-radius:2px;"></section>',
        )

    if level == 2:
        part = _part_label(block.level, section_number)
        return _template(
            theme,
            "heading",
            section_style="margin-top:30px;",
            part_block=f'<p style="margin:0 0 14px 0;"><span style="background-color:{primary};color:#ffffff;font-size:12px;font-weight:bold;padding:3px 12px;border-radius:8px;letter-spacing:1px;">{part}</span></p>',
            title_style="font-size:20px;font-weight:bold;color:#1a1a1a;margin:0 0 14px 0;line-height:1.6;",
            content=_inline(block.content, theme),
            title_decoration="",
        )

    return _template(
        theme,
        "heading",
        section_style=f"margin-top:24px;margin-bottom:12px;border-left:4px solid {primary};padding-left:12px;",
        part_block="",
        title_style="font-size:17px;font-weight:bold;color:#1a1a1a;margin:0;line-height:1.6;",
        content=_inline(block.content, theme),
        title_decoration="",
    )


def _unordered_list_item(theme: Theme, content: str) -> str:
    primary = theme.config.get("primary", PRIMARY)
    return (
        '<p style="margin:0 0 8px 0;color:#555555;line-height:1.9;">'
        f'<span style="display:inline-block;width:14px;color:{primary};font-weight:bold;">&bull;</span>'
        f'<span>{_inline(content, theme)}</span>'
        '</p>'
    )


def _ordered_list_item(theme: Theme, number: str, content: str) -> str:
    primary = theme.config.get("primary", PRIMARY)
    return (
        '<p style="margin:0 0 8px 0;color:#555555;line-height:1.9;">'
        f'<span style="display:inline-block;min-width:22px;color:{primary};font-weight:bold;">{number}.</span>'
        f'<span>{_inline(content, theme)}</span>'
        '</p>'
    )


def _inline(text: str, theme: Theme) -> str:
    primary = theme.config.get("primary", PRIMARY)
    escaped = html.escape(unescape_markdown_text(text.strip()))
    escaped = re.sub(
        r"`([^`]+)`",
        lambda match: f'<span style="font-family:Menlo,Consolas,monospace;background-color:#F3F4F6;padding:1px 4px;border-radius:4px;">{match.group(1)}</span>',
        escaped,
    )
    escaped = re.sub(
        r"\*\*(.+?)\*\*",
        lambda match: f'<strong style="color:{primary};font-weight:bold;">{match.group(1)}</strong>',
        escaped,
    )
    escaped = re.sub(
        r"__(.+?)__",
        lambda match: f'<strong style="color:{primary};font-weight:bold;">{match.group(1)}</strong>',
        escaped,
    )
    escaped = re.sub(
        r"&lt;u&gt;(.+?)&lt;/u&gt;",
        lambda match: f'<span style="text-decoration:underline;text-underline-offset:3px;">{match.group(1)}</span>',
        escaped,
    )
    escaped = re.sub(
        r"\+\+(.+?)\+\+",
        lambda match: f'<span style="text-decoration:underline;text-underline-offset:3px;">{match.group(1)}</span>',
        escaped,
    )
    return escaped


def _strip_html_comments(html_text: str) -> str:
    return re.sub(r"\s*<!--.*?-->\s*", "\n", html_text, flags=re.DOTALL)


def _inline_multiline(text: str, theme: Theme) -> str:
    lines = [_inline(line, theme) for line in text.splitlines() if line.strip()]
    return "<br>".join(lines)


def _part_label(level: int | None, section_number: int | None) -> str:
    if level != 2:
        return ""
    return f"Part {section_number}" if section_number is not None else "Part"


def _default_card_title(kind: str) -> str:
    return {
        "tip": "提示",
        "example": "示例",
        "pros": "正例",
        "cons": "反例",
    }.get(kind, "重点")
