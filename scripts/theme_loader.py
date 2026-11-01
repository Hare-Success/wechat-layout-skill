"""主题加载器：从 assets/themes/<主题名>.html 单文件读取主题配置和组件模板。

一个主题就是一个文件：
- ``<!-- @config {...} -->`` 注释块放配置（原 theme.json 的字段）；
- ``<!-- @component 名称 -->`` 标记切分组件模板，标记之间是模板原文；
- 组件必须覆盖 REQUIRED_COMPONENTS 列出的全部名字——这是渲染器与主题
  之间的接口契约（见 references/theme-contract.md）。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from string import Template
from typing import Any


# 主题必须提供的组件契约：与 renderer.py 的取用一一对应。
# 新增/改名组件时需同步更新此清单和 references/theme-contract.md。
REQUIRED_COMPONENTS = frozenset({
    "article",
    "card",
    "code",
    "divider",
    "heading-h1",
    "heading-h2",
    "heading-h3",
    "highlight",
    "image_placeholder",
    "inline-code",
    "list",
    "list-item-ol",
    "list-item-ul",
    "paragraph",
    "quote",
    "strong",
    "warning",
})

# 组件切分标记：独占一行，如 <!-- @component heading-h1 -->
_COMPONENT_RE = re.compile(r"<!--\s*@component\s+([A-Za-z0-9_-]+)\s*-->[ \t]*\n")
# 配置块：@config 与 --> 之间的 JSON，必须出现在第一个组件标记之前
_CONFIG_RE = re.compile(r"<!--\s*@config\s*(\{.*?\})\s*-->", re.DOTALL)


class Theme:
    """一个已加载的主题：主题文件路径、配置字典、组件名 → Template 的映射。"""

    def __init__(self, path: Path, config: dict[str, Any], components: dict[str, Template]) -> None:
        self.path = path
        self.config = config
        self.components = components

    def component(self, name: str) -> Template:
        """按组件名取模板，缺失时抛 KeyError（渲染要求主题必须提供该组件）。"""
        if name not in self.components:
            raise KeyError(f"主题缺少组件：{name}")
        return self.components[name]


def _parse_theme_file(text: str) -> tuple[dict[str, Any], dict[str, Template]]:
    """把单文件主题文本拆成（配置字典, 组件模板字典）。

    组件体取两个 @component 标记之间的原文，仅去掉尾部换行；
    组件体自带的说明注释原样保留，渲染收尾时统一剥除。
    """
    parts = _COMPONENT_RE.split(text)
    # parts 结构：[首个标记前的文本, 名1, 体1, 名2, 体2, ...]
    config_match = _CONFIG_RE.search(parts[0])
    config = json.loads(config_match.group(1)) if config_match else {}
    components = {
        name: Template(body.rstrip("\n"))
        for name, body in zip(parts[1::2], parts[2::2])
    }
    return config, components


def load_theme(theme_name: str, themes_dir: str | Path | None = None) -> Theme:
    """加载指定主题。

    Args:
        theme_name: 主题名，对应 assets/themes/<主题名>.html 单文件。
        themes_dir: 主题根目录，默认取项目内的 assets/themes。

    Returns:
        加载好的 Theme；主题文件不存在或缺少必需组件时抛 FileNotFoundError。
    """
    base = Path(themes_dir) if themes_dir else Path(__file__).resolve().parents[1] / "assets" / "themes"
    theme_file = base / f"{theme_name}.html"
    if not theme_file.exists():
        raise FileNotFoundError(f"主题不存在：{theme_file}（主题应为 assets/themes/<主题名>.html 单文件）")

    # utf-8-sig 容忍带 BOM 的文件；统一换行符方便标记匹配
    text = theme_file.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    config, components = _parse_theme_file(text)

    # 契约校验：缺组件时直接列出缺哪些，方便主题作者补齐
    missing = sorted(REQUIRED_COMPONENTS - components.keys())
    if missing:
        raise FileNotFoundError(
            f"主题 {theme_file.name} 缺少必需组件：{', '.join(missing)}"
            f"（文件内应有对应的 <!-- @component 名称 --> 段，见 references/theme-contract.md）"
        )
    return Theme(path=theme_file, config=config, components=components)
