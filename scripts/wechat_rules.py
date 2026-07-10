from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


FORBIDDEN_TAGS = {
    "script",
    "link",
    "style",
    "iframe",
    "object",
    "embed",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
}

FORBIDDEN_ATTRS = {
    "class",
    "id",
    "onclick",
    "onload",
    "onerror",
    "onmouseover",
}

FORBIDDEN_CSS_SNIPPETS = {
    "display:flex",
    "display: flex",
    "display:grid",
    "display: grid",
    "position:absolute",
    "position: absolute",
    "position:fixed",
    "position: fixed",
    "float:",
    "linear-gradient",
    "@media",
}


@dataclass(frozen=True)
class RuleViolation:
    rule: str
    detail: str


def validate_html(html: str) -> list[RuleViolation]:
    violations: list[RuleViolation] = []
    lowered = html.lower()

    for tag in sorted(FORBIDDEN_TAGS):
        if re.search(rf"<\s*/?\s*{re.escape(tag)}\b", lowered):
            violations.append(RuleViolation("forbidden_tag", f"<{tag}> is not allowed"))

    for attr in sorted(FORBIDDEN_ATTRS):
        if re.search(rf"\s{re.escape(attr)}\s*=", lowered):
            violations.append(RuleViolation("forbidden_attribute", f"{attr}= is not allowed"))

    for snippet in sorted(FORBIDDEN_CSS_SNIPPETS):
        if snippet in lowered:
            violations.append(RuleViolation("forbidden_css", f"{snippet} is not allowed"))

    if "<div" in lowered or "</div" in lowered:
        violations.append(RuleViolation("unstable_container", "Use <section> instead of <div>"))

    return violations


def validate_file(path: str | Path) -> list[RuleViolation]:
    html = Path(path).read_text(encoding="utf-8")
    return validate_html(html)


def format_violations(violations: list[RuleViolation]) -> str:
    return "\n".join(f"- {item.rule}: {item.detail}" for item in violations)
