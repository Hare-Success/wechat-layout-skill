"""CLI 校验入口：检查主题组件模板是否符合公众号 HTML 规则。

接受主题目录、组件目录或单个 HTML 文件，逐个输出校验结果；
任一文件违规时退出码为 1，便于接入 CI。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 允许直接以脚本方式运行，把项目根目录加入模块搜索路径
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.wechat_rules import format_violations, validate_file


def main() -> int:
    """解析命令行参数并校验模板，全部通过返回 0，否则返回 1。"""
    parser = argparse.ArgumentParser(description="校验主题组件模板是否符合公众号 HTML 规则。")
    parser.add_argument("path", help="主题目录、组件目录或单个 HTML 模板")
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        raise FileNotFoundError(target)

    # 目录则递归收集所有 .html 模板，单文件直接校验
    files = [target] if target.is_file() else sorted(target.rglob("*.html"))
    failed = False

    for file_path in files:
        violations = validate_file(file_path)
        if violations:
            failed = True
            print(f"{file_path}: 校验失败")
            print(format_violations(violations))
        else:
            print(f"{file_path}: 通过")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
