from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.parser import dump_ast, parse_markdown_file
from scripts.renderer import render
from scripts.theme_loader import load_theme


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Markdown to WeChat Official Account inline HTML.")
    parser.add_argument("input", help="Markdown file path")
    parser.add_argument("--theme", default="testModel", help="Theme name under assets/themes")
    parser.add_argument("--output", "-o", help="Output HTML path")
    parser.add_argument("--ast", help="Optional AST JSON output path")
    parser.add_argument("--no-validate", action="store_true", help="Skip WeChat HTML validation")
    args = parser.parse_args()

    input_path = Path(args.input)
    blocks = parse_markdown_file(input_path)
    theme = load_theme(args.theme)
    output_html = render(blocks, theme, validate=not args.no_validate)

    output_path = Path(args.output) if args.output else input_path.with_suffix(".wechat.html")
    output_path.write_text(output_html, encoding="utf-8")

    if args.ast:
        dump_ast(blocks, args.ast)

    print(f"Rendered {input_path} -> {output_path}")
    if args.ast:
        print(f"AST written to {args.ast}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
