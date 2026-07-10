from __future__ import annotations

import json
from pathlib import Path
from string import Template
from typing import Any


class Theme:
    def __init__(self, root: Path, config: dict[str, Any], components: dict[str, Template]) -> None:
        self.root = root
        self.config = config
        self.components = components

    def component(self, name: str) -> Template:
        if name not in self.components:
            raise KeyError(f"Theme component not found: {name}")
        return self.components[name]


def load_theme(theme_name: str, themes_dir: str | Path | None = None) -> Theme:
    base = Path(themes_dir) if themes_dir else Path(__file__).resolve().parents[1] / "assets" / "themes"
    root = base / theme_name
    if not root.exists():
        raise FileNotFoundError(f"Theme not found: {root}")

    config_path = root / "theme.json"
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}

    component_dir = root / "components"
    components = {
        path.stem: Template(path.read_text(encoding="utf-8"))
        for path in component_dir.glob("*.html")
    }
    return Theme(root=root, config=config, components=components)
