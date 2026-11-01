"""Markdown → Block AST 解析器。

流水线的第一步：把 Markdown 文本解析成 Block 列表，供 renderer.py 套用主题模板渲染。
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Block:
    """Markdown 的块级元素（段落、标题、列表、代码块、卡片等），是解析与渲染之间传递的 AST 节点。"""

    type: str  # 块类型：heading / paragraph / quote / code / *_list / card / divider / image_placeholder
    content: str = ""  # 主要文本内容（列表块不用，用 items）
    level: int | None = None  # 标题级别 1-6
    lang: str = ""  # 代码块语言标记
    items: list[str] = field(default_factory=list)  # 列表项文本
    title: str = ""  # 卡片标题
    meta: dict[str, Any] = field(default_factory=dict)  # 附加信息：卡片 kind、有序列表 start 等


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
UNORDERED_ITEM_RE = re.compile(r"^\s*[-*+]\s+(.+?)\s*$")
ORDERED_ITEM_RE = re.compile(r"^\s*(\d+)[.)]\s+(.+?)\s*$")
FENCE_RE = re.compile(r"^(?:```|~~~)\s*(.*?)\s*$")
CARD_RE = re.compile(r"^:::(card|tip|highlight|example|pros|cons|note|warning)\s*(.*?)\s*$", re.IGNORECASE)


def parse_markdown_file(path: str | Path) -> list[Block]:
    """读取 Markdown 文件并解析为 Block 列表；utf-8-sig 用于容忍带 BOM 的文件。"""
    return parse_markdown(Path(path).read_text(encoding="utf-8-sig"))


def parse_markdown(text: str) -> list[Block]:
    """把 Markdown 文本解析为 Block 列表。

    逐行扫描，按优先级依次尝试匹配代码块、卡片、标题、分隔线、
    图片占位符、引用、列表，都不匹配时按普通段落处理。
    """
    lines = [
        _normalize_markdown_controls(line)
        for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    ]
    blocks: list[Block] = []
    i = 0

    # 文件以 --- 开头视为 front matter，直接跳过
    if lines[:1] == ["---"]:
        i = _skip_front_matter(lines)

    while i < len(lines):
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        fence = FENCE_RE.match(line)
        if fence:
            block, i = _parse_code_block(lines, i, fence.group(1).strip())
            blocks.append(block)
            continue

        card = CARD_RE.match(line)
        if card:
            block, i = _parse_card_block(lines, i, card.group(1).lower(), card.group(2).strip())
            blocks.append(block)
            continue

        heading = HEADING_RE.match(line)
        if heading:
            blocks.append(Block(type="heading", level=len(heading.group(1)), content=heading.group(2).strip()))
            i += 1
            continue

        if _is_divider(line):
            blocks.append(Block(type="divider"))
            i += 1
            continue

        if _is_image_placeholder(line):
            blocks.append(Block(type="image_placeholder", content=line.strip()))
            i += 1
            continue

        if line.lstrip().startswith(">"):
            block, i = _parse_quote(lines, i)
            blocks.append(block)
            continue

        if UNORDERED_ITEM_RE.match(line):
            block, i = _parse_list(lines, i, ordered=False)
            blocks.append(block)
            continue

        if ORDERED_ITEM_RE.match(line):
            block, i = _parse_list(lines, i, ordered=True)
            blocks.append(block)
            continue

        block, i = _parse_paragraph(lines, i)
        blocks.append(block)

    return blocks


def blocks_to_dicts(blocks: list[Block]) -> list[dict[str, Any]]:
    """把 Block 列表转成 dict 列表，便于 JSON 序列化。"""
    return [asdict(block) for block in blocks]


def dump_ast(blocks: list[Block], path: str | Path) -> None:
    """把 Block AST 以 JSON 形式写入文件（供调试/排查）。"""
    Path(path).write_text(json.dumps(blocks_to_dicts(blocks), ensure_ascii=False, indent=2), encoding="utf-8")


def _skip_front_matter(lines: list[str]) -> int:
    """跳过 YAML front matter，返回正文第一行的下标；找不到结尾 --- 则返回 0 从头解析。"""
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return index + 1
    return 0


def _normalize_markdown_controls(line: str) -> str:
    r"""兼容从转义环境复制来的 Markdown，例如 \# 或 1\.。"""
    line = re.sub(r"^(\s*)\\(#{1,6}\s+)", r"\1\2", line)
    line = re.sub(r"^(\s*)\\([-*+]\s+)", r"\1\2", line)
    line = re.sub(r"^(\s*\d+)\\([.)]\s+)", r"\1\2", line)
    line = re.sub(r"^(\s*)\\(---|\*\*\*|___)\s*$", r"\1\2", line)
    line = re.sub(r"^(\s*)\\(>\s*)", r"\1\2", line)
    return line


def unescape_markdown_text(text: str) -> str:
    r"""去掉文本中 Markdown 特殊字符前的转义反斜杠，如 \_ → _。"""
    return re.sub(r"\\([_#*+\-.!{}\[\]()])", r"\1", text)


def _parse_code_block(lines: list[str], start: int, lang: str) -> tuple[Block, int]:
    """解析围栏代码块（``` / ~~~）。返回代码块和下一行的下标；缺少闭合围栏时读到文件末尾。"""
    content: list[str] = []
    i = start + 1
    while i < len(lines):
        if lines[i].startswith("```") or lines[i].startswith("~~~"):
            return Block(type="code", content="\n".join(content), lang=lang), i + 1
        content.append(lines[i])
        i += 1
    return Block(type="code", content="\n".join(content), lang=lang), i


def _parse_card_block(lines: list[str], start: int, kind: str, raw_title: str) -> tuple[Block, int]:
    """解析 :::kind 卡片块（Docusaurus 风格）。返回卡片块和下一行的下标；缺少闭合 ::: 时读到文件末尾。"""
    content: list[str] = []
    i = start + 1
    while i < len(lines):
        if lines[i].strip() == ":::":
            cleaned_title = _extract_bracket_title(raw_title)
            return Block(type="card", content="\n".join(content).strip(), title=cleaned_title, meta={"kind": kind}), i + 1
        content.append(lines[i])
        i += 1
    cleaned_title = _extract_bracket_title(raw_title)
    return Block(type="card", content="\n".join(content).strip(), title=cleaned_title, meta={"kind": kind}), i



def _extract_bracket_title(raw: str) -> str:
    """从 Docusaurus 风格的中括号写法中提取标题，例如 :::note[我的标题]。"""
    m = re.match(r"^\[([^\]]*)\](?:\s+(.*))?$", raw)
    return m.group(1).strip() if m else raw


def _parse_quote(lines: list[str], start: int) -> tuple[Block, int]:
    """解析连续的 > 引用行，合并为一个引用块。返回引用块和下一行的下标。"""
    content: list[str] = []
    i = start
    while i < len(lines) and lines[i].lstrip().startswith(">"):
        content.append(lines[i].lstrip()[1:].strip())
        i += 1
    return Block(type="quote", content="\n".join(content).strip()), i


def _parse_list(lines: list[str], start: int, ordered: bool) -> tuple[Block, int]:
    """解析有序/无序列表。返回列表块和下一行的下标。"""
    items: list[str] = []
    pattern = ORDERED_ITEM_RE if ordered else UNORDERED_ITEM_RE
    start_number: int | None = None
    i = start
    while i < len(lines):
        match = pattern.match(lines[i])
        if match:
            if ordered:
                if start_number is None:
                    start_number = int(match.group(1))
                items.append(match.group(2).strip())
            else:
                items.append(match.group(1).strip())
            i += 1
            continue

        if lines[i].strip():
            break

        # 空行不一定结束列表：向后跳过连续空行，若下一行仍是同类列表项，
        # 说明只是列表项之间的空行，继续收集；否则列表才真正结束
        next_item = i + 1
        while next_item < len(lines) and not lines[next_item].strip():
            next_item += 1
        if next_item < len(lines) and pattern.match(lines[next_item]):
            i = next_item
            continue
        break
    # 有序列表记录起始编号（如从 3. 开始），渲染时按它连续编号
    meta = {"start": start_number or 1} if ordered else {}
    return Block(type="ordered_list" if ordered else "unordered_list", items=items, meta=meta), i


def _parse_paragraph(lines: list[str], start: int) -> tuple[Block, int]:
    """解析普通段落：收集连续文本行直到空行或其他块级语法。返回段落块和下一行的下标。"""
    content: list[str] = []
    i = start
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            break
        if _starts_special_block(line):
            break
        content.append(line.strip())
        i += 1
    # Markdown 段落内的换行在渲染时视为空格，这里直接拼成一行
    return Block(type="paragraph", content=" ".join(content).strip()), i


def _starts_special_block(line: str) -> bool:
    """判断当前行是否开启了某种块级语法（用于终止段落收集）。"""
    return bool(
        FENCE_RE.match(line)
        or CARD_RE.match(line)
        or HEADING_RE.match(line)
        or _is_divider(line)
        or _is_image_placeholder(line)
        or line.lstrip().startswith(">")
        or UNORDERED_ITEM_RE.match(line)
        or ORDERED_ITEM_RE.match(line)
    )


def _is_divider(line: str) -> bool:
    """判断是否为水平分隔线（---、***、___）。"""
    stripped = line.strip()
    return stripped in {"---", "***", "___"}


def _is_image_placeholder(line: str) -> bool:
    """判断是否为图片占位符（几种文字占位写法或 Markdown 图片语法）。"""
    stripped = line.strip()
    return stripped in {"插入图片", "[image]", "[[image]]", "{{image}}"} or stripped.startswith("![")
