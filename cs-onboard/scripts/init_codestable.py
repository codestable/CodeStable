from __future__ import annotations

import argparse
from pathlib import Path


FACTS = """# facts.md

## 启动必读事实

- [一句当前最影响判断的稳定事实]

## 流程索引

- [做某个已跑通流程前，先读 .cs/notes/YYYY/MM/DD/{slug}.md]
"""

DIRS = [
    ".cs/talks",
    ".cs/issues",
    ".cs/epics",
    ".cs/requirements",
    ".cs/notes",
    ".cs/tools",
]


def init_codestable(project: Path, force: bool) -> int:
    project = project.resolve()

    for rel in DIRS:
        (project / rel).mkdir(parents=True, exist_ok=True)

    facts = project / ".cs" / "facts.md"
    created: list[str] = []
    kept: list[str] = []

    if facts.exists() and not force:
        kept.append(str(facts))
    else:
        facts.write_text(FACTS, encoding="utf-8")
        created.append(str(facts))

    print(f"Initialized CodeStable workspace at {project / '.cs'}")
    print(f"Created or updated files: {len(created)}")
    for path in created:
        print(f"  + {path}")
    if kept:
        print(f"Kept existing files: {len(kept)}")
        for path in kept:
            print(f"  = {path}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a CodeStable .cs workspace.")
    parser.add_argument("--project", default=".", help="Project root to initialize.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing template files.")
    args = parser.parse_args()

    return init_codestable(Path(args.project), args.force)


if __name__ == "__main__":
    raise SystemExit(main())
