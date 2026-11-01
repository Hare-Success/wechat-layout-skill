"""公众号 HTML 规则校验。

流水线的最后一道关卡：公众号编辑器对 HTML 有诸多限制，
这里校验产物/模板是否触碰禁用标签、禁用属性和禁用 CSS 写法。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


# 禁用标签：公众号会剥离 script/style/link 等，也不支持 h1-h6（标题须用 section 模拟）
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

# 禁用属性：公众号会过滤 class/id 和事件处理属性，样式必须全部内联
FORBIDDEN_ATTRS = {
    "class",
    "id",
    "onclick",
    "onload",
    "onerror",
    "onmouseover",
}

# 禁用 CSS 写法：flex/grid/定位/浮动/渐变/媒体查询在公众号里表现不稳定或会被过滤
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
    """一条规则违规记录：规则名 + 具体说明。"""

    rule: str
    detail: str


def validate_html(html: str) -> list[RuleViolation]:
    """校验 HTML 文本，返回所有违规项（空列表表示通过）。"""
    violations: list[RuleViolation] = []
    # 全文转小写后匹配，避免大小写绕过（如 <SCRIPT>）
    lowered = html.lower()

    for tag in sorted(FORBIDDEN_TAGS):
        if re.search(rf"<\s*/?\s*{re.escape(tag)}\b", lowered):
            violations.append(RuleViolation("forbidden_tag", f"不允许使用 <{tag}> 标签"))

    for attr in sorted(FORBIDDEN_ATTRS):
        if re.search(rf"\s{re.escape(attr)}\s*=", lowered):
            violations.append(RuleViolation("forbidden_attribute", f"不允许使用 {attr}= 属性"))

    for snippet in sorted(FORBIDDEN_CSS_SNIPPETS):
        if snippet in lowered:
            violations.append(RuleViolation("forbidden_css", f"不允许使用 {snippet}"))

    # div 在公众号编辑器里会被改写/嵌套异常，统一用 section 作为容器
    if "<div" in lowered or "</div" in lowered:
        violations.append(RuleViolation("unstable_container", "请使用 <section> 代替 <div>"))

    return violations


def validate_file(path: str | Path) -> list[RuleViolation]:
    """读取文件并校验其 HTML 内容，返回违规项列表。"""
    html = Path(path).read_text(encoding="utf-8")
    return validate_html(html)


def format_violations(violations: list[RuleViolation]) -> str:
    """把违规项格式化成每行一条的文本，供 CLI 输出。"""
    return "\n".join(f"- {item.rule}: {item.detail}" for item in violations)
