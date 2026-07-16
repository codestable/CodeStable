from __future__ import annotations

import argparse
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_ROOT / "templates" / "entities"

DIRS = [
    ".cs/talks",
    ".cs/vision",
    ".cs/spec",
    ".cs/issues",
    ".cs/epics",
    ".cs/notes",
    ".cs/tools",
]


def init_codestable(project: Path, force: bool) -> int:
    project = project.resolve()
    vision_template = (TEMPLATES / "vision-index.md").read_text(encoding="utf-8")
    project_spec_template = (TEMPLATES / "project-spec-index.md").read_text(encoding="utf-8")

    for rel in DIRS:
        (project / rel).mkdir(parents=True, exist_ok=True)

    managed_indexes = [
        (project / ".cs" / "vision" / "index.md", vision_template),
        (project / ".cs" / "spec" / "index.md", project_spec_template),
    ]
    created: list[str] = []
    kept: list[str] = []

    for index_path, template in managed_indexes:
        if index_path.exists() and not force:
            kept.append(str(index_path))
        else:
            index_path.write_text(template, encoding="utf-8")
            created.append(str(index_path))

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
    parser.add_argument("--force", action="store_true", help="Overwrite the existing vision and project spec indexes.")
    args = parser.parse_args()

    return init_codestable(Path(args.project), args.force)


if __name__ == "__main__":
    raise SystemExit(main())
