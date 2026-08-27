#!/usr/bin/env python3
"""Import a folder of Markdown files into content/posts.

Existing front matter is preserved. Files without front matter receive a title
and date inferred from their first H1, filename, or modification time.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
from pathlib import Path


DATE_IN_NAME = re.compile(r"(?P<date>\d{4}-\d{2}-\d{2})")
FIRST_H1 = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def yaml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def inferred_date(path: Path) -> str:
    match = DATE_IN_NAME.search(path.name)
    if match:
        return match.group("date")
    modified = dt.datetime.fromtimestamp(path.stat().st_mtime).astimezone()
    return modified.date().isoformat()


def inferred_slug(path: Path) -> str:
    slug = DATE_IN_NAME.sub("", path.stem).strip("-_ ")
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.lower() or path.stem.lower()


def inferred_title(path: Path, body: str) -> tuple[str, str]:
    match = FIRST_H1.search(body)
    if match:
        title = match.group(1).strip().strip("#").strip()
        body = body[: match.start()] + body[match.end() :]
        return title, body.lstrip("\r\n")
    title = DATE_IN_NAME.sub("", path.stem).strip("-_ ")
    title = title.replace("_", " ").replace("-", " ").strip()
    return title or path.stem, body


def ensure_front_matter(path: Path, text: str) -> str:
    if text.startswith("---\n") or text.startswith("---\r\n"):
        lines = text.splitlines(keepends=True)
        closing = next(
            (i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"),
            None,
        )
        if closing is None:
            raise ValueError("front matter 没有结束分隔符 ---")

        front = "".join(lines[1:closing])
        additions: list[str] = []
        if not re.search(r"(?m)^title\s*:", front):
            title, _ = inferred_title(path, "".join(lines[closing + 1 :]))
            additions.append(f"title: {yaml_string(title)}\n")
        if not re.search(r"(?m)^date\s*:", front):
            additions.append(f"date: {inferred_date(path)}T00:00:00+08:00\n")
        if not re.search(r"(?m)^slug\s*:", front):
            additions.append(f"slug: {yaml_string(inferred_slug(path))}\n")
        if not additions:
            return text
        return "".join(lines[:closing] + additions + lines[closing:])

    title, body = inferred_title(path, text)
    front = (
        "---\n"
        f"title: {yaml_string(title)}\n"
        f"slug: {yaml_string(inferred_slug(path))}\n"
        f"date: {inferred_date(path)}T00:00:00+08:00\n"
        "draft: false\n"
        "tags: []\n"
        "---\n\n"
    )
    return front + body.lstrip()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="将一个目录中的 Markdown 递归导入 Hugo content/posts"
    )
    parser.add_argument("source", type=Path, help="现有 Markdown 文件夹")
    parser.add_argument(
        "--destination",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "content" / "posts" / "imported",
        help="目标目录，默认 content/posts/imported",
    )
    parser.add_argument(
        "--force", action="store_true", help="覆盖目标目录中同名的 Markdown"
    )
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    destination = args.destination.expanduser().resolve()
    if not source.is_dir():
        parser.error(f"源目录不存在：{source}")
    if source == destination or source in destination.parents:
        parser.error("目标目录不能位于源目录内部")

    files = sorted(
        p
        for p in source.rglob("*.md")
        if p.is_file()
        and not p.name.startswith("_")
        and p.name.casefold() != "readme.md"
    )
    if not files:
        print(f"没有找到 Markdown：{source}")
        return 0

    imported = 0
    skipped = 0
    for src in files:
        rel = src.relative_to(source)
        dst = destination / rel
        if dst.exists() and not args.force:
            print(f"跳过已存在文件：{dst}")
            skipped += 1
            continue
        try:
            text = src.read_text(encoding="utf-8-sig")
            rendered = ensure_front_matter(src, text)
        except (UnicodeDecodeError, ValueError) as exc:
            print(f"跳过无法导入的文件：{src}（{exc}）")
            skipped += 1
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(rendered, encoding="utf-8")
        shutil.copystat(src, dst)
        print(f"导入：{src} -> {dst}")
        imported += 1

    print(f"完成：导入 {imported} 篇，跳过 {skipped} 篇。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
