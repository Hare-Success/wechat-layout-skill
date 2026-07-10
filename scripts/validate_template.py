from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.wechat_rules import format_violations, validate_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate theme component templates against WeChat HTML rules.")
    parser.add_argument("path", help="Theme directory, component directory, or single HTML template")
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        raise FileNotFoundError(target)

    files = [target] if target.is_file() else sorted(target.rglob("*.html"))
    failed = False

    for file_path in files:
        violations = validate_file(file_path)
        if violations:
            failed = True
            print(f"{file_path}: failed")
            print(format_violations(violations))
        else:
            print(f"{file_path}: ok")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
