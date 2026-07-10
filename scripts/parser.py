from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Block:
    type: str
    content: str = ""
    level: int | None = None
    lang: str = ""
    items: list[str] = field(default_factory=list)
    title: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
UNORDERED_ITEM_RE = re.compile(r"^\s*[-*+]\s+(.+?)\s*$")
ORDERED_ITEM_RE = re.compile(r"^\s*(\d+)[.)]\s+(.+?)\s*$")
FENCE_RE = re.compile(r"^```\s*([^`]*)\s*$")
CARD_RE = re.compile(r"^:::(card|tip|highlight|example|pros|cons)\s*(.*?)\s*$", re.IGNORECASE)


def parse_markdown_file(path: str | Path) -> list[Block]:
    return parse_markdown(Path(path).read_text(encoding="utf-8-sig"))


def parse_markdown(text: str) -> list[Block]:
    lines = [
        _normalize_markdown_controls(line)
        for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    ]
    blocks: list[Block] = []
    i = 0

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
    return [asdict(block) for block in blocks]


def dump_ast(blocks: list[Block], path: str | Path) -> None:
    Path(path).write_text(json.dumps(blocks_to_dicts(blocks), ensure_ascii=False, indent=2), encoding="utf-8")


def _skip_front_matter(lines: list[str]) -> int:
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return index + 1
    return 0


def _normalize_markdown_controls(line: str) -> str:
    r"""Accept Markdown copied from escaped contexts, for example \# or 1\."""
    line = re.sub(r"^(\s*)\\(#{1,6}\s+)", r"\1\2", line)
    line = re.sub(r"^(\s*)\\([-*+]\s+)", r"\1\2", line)
    line = re.sub(r"^(\s*\d+)\\([.)]\s+)", r"\1\2", line)
    line = re.sub(r"^(\s*)\\(---|\*\*\*|___)\s*$", r"\1\2", line)
    line = re.sub(r"^(\s*)\\(>\s*)", r"\1\2", line)
    return line


def unescape_markdown_text(text: str) -> str:
    return re.sub(r"\\([_#*+\-.!{}\[\]()])", r"\1", text)


def _parse_code_block(lines: list[str], start: int, lang: str) -> tuple[Block, int]:
    content: list[str] = []
    i = start + 1
    while i < len(lines):
        if lines[i].startswith("```"):
            return Block(type="code", content="\n".join(content), lang=lang), i + 1
        content.append(lines[i])
        i += 1
    return Block(type="code", content="\n".join(content), lang=lang), i


def _parse_card_block(lines: list[str], start: int, kind: str, title: str) -> tuple[Block, int]:
    content: list[str] = []
    i = start + 1
    while i < len(lines):
        if lines[i].strip() == ":::":
            return Block(type="card", content="\n".join(content).strip(), title=title, meta={"kind": kind}), i + 1
        content.append(lines[i])
        i += 1
    return Block(type="card", content="\n".join(content).strip(), title=title, meta={"kind": kind}), i


def _parse_quote(lines: list[str], start: int) -> tuple[Block, int]:
    content: list[str] = []
    i = start
    while i < len(lines) and lines[i].lstrip().startswith(">"):
        content.append(lines[i].lstrip()[1:].strip())
        i += 1
    return Block(type="quote", content="\n".join(content).strip()), i


def _parse_list(lines: list[str], start: int, ordered: bool) -> tuple[Block, int]:
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

        next_item = i + 1
        while next_item < len(lines) and not lines[next_item].strip():
            next_item += 1
        if next_item < len(lines) and pattern.match(lines[next_item]):
            i = next_item
            continue
        break
    meta = {"start": start_number or 1} if ordered else {}
    return Block(type="ordered_list" if ordered else "unordered_list", items=items, meta=meta), i


def _parse_paragraph(lines: list[str], start: int) -> tuple[Block, int]:
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
    return Block(type="paragraph", content=" ".join(content).strip()), i


def _starts_special_block(line: str) -> bool:
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
    stripped = line.strip()
    return stripped in {"---", "***", "___"}


def _is_image_placeholder(line: str) -> bool:
    stripped = line.strip()
    return stripped in {"插入图片", "[image]", "[[image]]", "{{image}}"} or stripped.startswith("![")
