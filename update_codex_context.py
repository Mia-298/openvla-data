"""Append a concise Codex task context entry to CODEX_CONTEXT.md."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", required=True)
    parser.add_argument("--progress", required=True)
    parser.add_argument("--next-step", required=True)
    parser.add_argument("--summary", required=True)
    args = parser.parse_args()

    context_path = Path(__file__).with_name("CODEX_CONTEXT.md")
    if not context_path.exists():
        context_path.write_text(
            "# Codex Project Context\n\n"
            "This file stores concise cross-device task context.\n\n",
            encoding="utf-8",
        )

    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    entry = (
        f"## {timestamp}\n\n"
        f"- Keywords: {args.keywords}\n"
        f"- Progress: {args.progress}\n"
        f"- Next step: {args.next_step}\n"
        f"- Summary: {args.summary}\n\n"
    )
    with context_path.open("a", encoding="utf-8") as stream:
        stream.write(entry)


if __name__ == "__main__":
    main()
