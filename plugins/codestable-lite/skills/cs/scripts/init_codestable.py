from __future__ import annotations

import argparse
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_ROOT / "templates" / "entities"

DIRS = [
    ".cs/talks",
    ".cs/spec",
    ".cs/issues",
    ".cs/epics",
    ".cs/notes",
    ".cs/tools",
]


def init_codestable(project: Path, force: bool) -> int:
    project = project.resolve()
    facts_template = (TEMPLATES / "facts.md").read_text(encoding="utf-8")
    project_spec_template = (TEMPLATES / "project-spec-index.md").read_text(encoding="utf-8")

    for rel in DIRS:
        (project / rel).mkdir(parents=True, exist_ok=True)

    facts = project / ".cs" / "facts.md"
    project_spec_index = project / ".cs" / "spec" / "index.md"
    created: list[str] = []
    kept: list[str] = []

    if facts.exists() and not force:
        kept.append(str(facts))
    else:
        facts.write_text(facts_template, encoding="utf-8")
        created.append(str(facts))

    if project_spec_index.exists() and not force:
        kept.append(str(project_spec_index))
    else:
        project_spec_index.write_text(project_spec_template, encoding="utf-8")
        created.append(str(project_spec_index))

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
