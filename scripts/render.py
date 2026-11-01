"""CLI 渲染入口：Markdown 文件 → 公众号内联样式 HTML。

串联完整流水线：parse（parser）→ load_theme（theme_loader）→ render（renderer，含校验），
可选同时输出 AST JSON 供调试。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 允许直接以脚本方式运行（python scripts/render.py），把项目根目录加入模块搜索路径
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.parser import dump_ast, parse_markdown_file
from scripts.renderer import render
from scripts.theme_loader import load_theme


def main() -> int:
    """解析命令行参数并执行渲染，返回进程退出码。"""
    parser = argparse.ArgumentParser(description="将 Markdown 渲染为微信公众号内联样式 HTML。")
    parser.add_argument("input", help="Markdown 文件路径")
    parser.add_argument("--theme", default="tech-ai", help="assets/themes 下的主题名")
    parser.add_argument("--output", "-o", help="输出 HTML 路径")
    parser.add_argument("--ast", help="可选的 AST JSON 输出路径")
    parser.add_argument("--no-validate", action="store_true", help="跳过公众号 HTML 规则校验")
    args = parser.parse_args()

    input_path = Path(args.input)
    blocks = parse_markdown_file(input_path)
    theme = load_theme(args.theme)
    output_html = render(blocks, theme, validate=not args.no_validate)

    output_path = Path(args.output) if args.output else input_path.with_suffix(".wechat.html")
    output_path.write_text(output_html, encoding="utf-8")

    if args.ast:
        dump_ast(blocks, args.ast)

    print(f"已渲染 {input_path} -> {output_path}")
    if args.ast:
        print(f"AST 已写入 {args.ast}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
