"""校验 cs-* skill 的 frontmatter `contracts` 对 SKILL.md body 成立。

contracts 是 prompt-as-code 的机器护栏：`grep` 锚点保护关键骨架不被删，
`not-grep` 锚点禁止危险/退化写法。此前 CodeStable 本地没有校验器，
contracts 只是声明；本测试让它们真正生效。

关键：只扫 **body**（剥掉 frontmatter），否则 `not-grep` 会命中 frontmatter
里 contract 声明行自身，造成假阳性。
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "plugins/codestable/skills"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)

# 刚经 build-cs-skill 重构、已声明 contracts 的主入口。删除其 contracts 应是
# 有意识的动作——此清单防止护栏被静默移除。
CORE_SKILLS_WITH_CONTRACTS = {
    "cs-feat", "cs-epic", "cs-issue", "cs-refactor", "cs-docs", "cs-goal",
    "cs-code-review", "cs-audit", "cs-domain", "cs-req",
}


def _split_frontmatter(text: str) -> tuple[str | None, str]:
    """返回 (frontmatter, body)。无 frontmatter 时 frontmatter 为 None。"""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None, text
    return match.group(1), match.group(2)


def _skills_with_contracts() -> list[Path]:
    found: list[Path] = []
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        frontmatter, _ = _split_frontmatter(path.read_text(encoding="utf-8"))
        if frontmatter and "contracts:" in frontmatter:
            found.append(path)
    return found


SKILLS_WITH_CONTRACTS = _skills_with_contracts()


@pytest.mark.parametrize(
    "skill_md", SKILLS_WITH_CONTRACTS, ids=lambda p: p.parent.name
)
def test_frontmatter_contracts_hold_against_body(skill_md: Path) -> None:
    frontmatter, body = _split_frontmatter(skill_md.read_text(encoding="utf-8"))
    meta = yaml.safe_load(frontmatter)
    contracts = meta.get("contracts") or []

    failures: list[str] = []
    for entry in contracts:
        if not isinstance(entry, dict) or (
            "grep" not in entry and "not-grep" not in entry
        ):
            failures.append(f"contract 缺 grep/not-grep: {entry!r}")
            continue
        # literal 子串匹配；只针对 body，不含 frontmatter 声明本身。
        if "grep" in entry and entry["grep"] not in body:
            failures.append(f"grep 锚点缺失: {entry['grep']!r}")
        if "not-grep" in entry and entry["not-grep"] in body:
            failures.append(f"not-grep 锚点命中: {entry['not-grep']!r}")

    assert not failures, (
        f"{skill_md.parent.name} contract 违反:\n  " + "\n  ".join(failures)
    )


def test_core_skills_declare_contracts() -> None:
    """cs-feat / cs-epic 必须保留 contracts，防止护栏被静默删除。"""
    declared = {p.parent.name for p in SKILLS_WITH_CONTRACTS}
    missing = CORE_SKILLS_WITH_CONTRACTS - declared
    assert not missing, f"这些主入口应声明 contracts 却未声明: {sorted(missing)}"


def test_not_grep_ignores_frontmatter_declaration() -> None:
    """回归护栏：校验器必须扫 body 而非全文件。

    cs-feat 的 frontmatter 含 `- not-grep: "git push"` 声明行；若校验器错误
    地扫全文件，会命中该行而误报。此测试锁死"只扫 body"的语义。
    """
    text = (SKILLS / "cs-feat" / "SKILL.md").read_text(encoding="utf-8")
    frontmatter, body = _split_frontmatter(text)
    assert frontmatter is not None
    assert 'not-grep: "git push"' in frontmatter  # 声明确实在 frontmatter
    assert "git push" not in body  # 但 body 干净——not-grep 应通过
