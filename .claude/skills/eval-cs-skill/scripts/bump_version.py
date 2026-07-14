#!/usr/bin/env python3
"""同步版本到打包检查要求的所有位置 + 追加 CHANGELOG。

真相源对齐 tools/check-plugin-package.py：VERSION 与
- plugins/codestable/skills/cs-onboard/VERSION
- plugins/codestable/.codex-plugin/plugin.json [version]
- plugins/codestable/.claude-plugin/plugin.json [version]
- .claude-plugin/marketplace.json [plugins,0,version]
- .agents/plugins/marketplace.json [plugins,0,version]
须一致；CHANGELOG.md 须有 `## {version}` 段。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from config import repo_root  # noqa: E402

SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")

# (相对路径, JSON 键路径 | None=纯文本 VERSION)
TARGETS = [
    ("VERSION", None),
    ("plugins/codestable/skills/cs-onboard/VERSION", None),
    ("plugins/codestable/.codex-plugin/plugin.json", ["version"]),
    ("plugins/codestable/.claude-plugin/plugin.json", ["version"]),
    (".claude-plugin/marketplace.json", ["plugins", 0, "version"]),
    (".agents/plugins/marketplace.json", ["plugins", 0, "version"]),
]


def _set_nested(data, keys, value):
    cur = data
    for k in keys[:-1]:
        cur = cur[k]
    cur[keys[-1]] = value


def bump(root: Path, version: str, note: str) -> list[str]:
    changed = []
    for rel, keys in TARGETS:
        path = root / rel
        if keys is None:
            path.write_text(version + "\n", encoding="utf-8")
        else:
            data = json.loads(path.read_text(encoding="utf-8"))
            _set_nested(data, keys, version)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        changed.append(rel)

    # CHANGELOG：若无 `## {version}` 段则在 `# Changelog` 后插入
    clog = root / "CHANGELOG.md"
    text = clog.read_text(encoding="utf-8")
    if f"## {version}" not in text and f"## [{version}]" not in text:
        section = f"## {version}\n\n- {note}\n\n"
        if text.startswith("# Changelog"):
            head, _, rest = text.partition("\n")
            text = head + "\n\n" + section + rest.lstrip("\n")
        else:
            text = section + text
        clog.write_text(text, encoding="utf-8")
        changed.append("CHANGELOG.md")
    return changed


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="同步 CodeStable 版本")
    p.add_argument("--to", required=True, help="目标 semver，如 1.1.0")
    p.add_argument("--note", default="eval-cs-skill release: evaluated + optimized skill update.")
    p.add_argument("--root")
    args = p.parse_args(argv)
    if not SEMVER.match(args.to):
        print(f"非 semver: {args.to}", file=sys.stderr)
        return 2
    root = Path(args.root).resolve() if args.root else repo_root()
    changed = bump(root, args.to, args.note)
    print(f"[eval-cs-skill] 版本 → {args.to}；已更新: {', '.join(changed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
