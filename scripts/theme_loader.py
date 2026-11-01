"""主题加载器：从 assets/themes/<主题名>/ 读取主题配置和组件模板。

主题由 theme.json（颜色等配置）和 components/*.html（$变量 占位符模板）组成，
供 renderer.py 渲染时取用。components 必须提供 REQUIRED_COMPONENTS 列出的
全部组件——这是渲染器与主题之间的接口契约。
"""

from __future__ import annotations

import json
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


class Theme:
    """一个已加载的主题：根目录、配置字典、组件名 → Template 的映射。"""

    def __init__(self, root: Path, config: dict[str, Any], components: dict[str, Template]) -> None:
        self.root = root
        self.config = config
        self.components = components

    def component(self, name: str) -> Template:
        """按组件名取模板，缺失时抛 KeyError（渲染要求主题必须提供该组件）。"""
        if name not in self.components:
            raise KeyError(f"主题缺少组件：{name}")
        return self.components[name]


def load_theme(theme_name: str, themes_dir: str | Path | None = None) -> Theme:
    """加载指定主题。

    Args:
        theme_name: 主题目录名，如 tech-ai。
        themes_dir: 主题根目录，默认取项目内的 assets/themes。

    Returns:
        加载好的 Theme；主题目录不存在或缺少必需组件时抛 FileNotFoundError。
    """
    base = Path(themes_dir) if themes_dir else Path(__file__).resolve().parents[1] / "assets" / "themes"
    root = base / theme_name
    if not root.exists():
        raise FileNotFoundError(f"主题不存在：{root}")

    config_path = root / "theme.json"
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}

    # components 目录下的每个 .html 文件即一个组件模板，文件名（去后缀）为组件名
    component_dir = root / "components"
    components = {
        path.stem: Template(path.read_text(encoding="utf-8"))
        for path in component_dir.glob("*.html")
    }

    # 契约校验：缺组件时直接列出缺哪些文件，方便主题作者补齐
    missing = sorted(REQUIRED_COMPONENTS - components.keys())
    if missing:
        raise FileNotFoundError(
            f"主题 {theme_name} 缺少必需组件：{', '.join(missing)}"
            f"（components/ 下应存在对应的 .html 文件，见 references/theme-contract.md）"
        )
    return Theme(root=root, config=config, components=components)
