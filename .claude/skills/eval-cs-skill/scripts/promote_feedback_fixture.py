#!/usr/bin/env python3
"""Promote a cs-feedback candidate into a repo-local experiment fixture."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from _model import Fixture  # noqa: E402
from buildprompt import build_prompt  # noqa: E402
from config import ExperimentConfig  # noqa: E402
from fixtures import validate_fixture_dict  # noqa: E402


ROUTING_INCIDENT_KINDS = {
    "wrong-route",
    "skipped-gate",
    "missing-artifact",
    "goal-driver",
    "unnecessary-detour",
}
FINDINGS_INCIDENT_KINDS = {
    "tool-failure",
    "install-version",
    "privacy-reporting",
    "unclear-rule",
}
TASK_KIND_BY_TARGET = {
    "cs-code-review": "review",
    "cs-issue": "fix",
    "cs-audit": "audit",
    "cs-feat": "design",
    "cs-refactor": "design",
    "cs-epic": "design",
    "cs-req": "design",
    "cs-domain": "design",
    "cs-docs": "docs",
    "cs-docs-neat": "docs",
}
MOCK_HARNESSES = {"mock", "mock-weak"}
PLACEHOLDER_PATTERN = re.compile(r"\b(?:TODO|TBD|unknown)\b", re.IGNORECASE)
SAFE_FIXTURE_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
SECRET_KEY_PATTERN = re.compile(
    r"""(?imx)['"]?(?P<key>api[_-]?key|token|secret|password|authorization|bearer)['"]?
    \s*[:=：＝]\s*"""
)
AUTHORIZATION_HEADER_PATTERN = re.compile(
    r"(?im)(?<![A-Za-z0-9])(?:(?:http|proxy)[-_])?authorization\s*[:=]\s*"
    r"[A-Za-z][A-Za-z0-9._~-]*\s+[^\r\n]+"
)
AUTH_SCHEME_PATTERN = re.compile(
    r"(?i)\b(?:(?:proxy-)?authorization\s*[:=]\s*)?"
    r"(?:basic|bearer)\s+[A-Za-z0-9._~+/=-]{6,}"
)
USER_CREDENTIAL_PATTERN = re.compile(
    r"(?ix)(?<!\S)(?:-u|--user)(?:\s+|=)"
    r"(?:\"[^\"\r\n]+\"|'[^'\r\n]+'|[^\s`'\"]+)"
)
CREDENTIAL_PATTERNS = (
    AUTHORIZATION_HEADER_PATTERN,
    USER_CREDENTIAL_PATTERN,
    AUTH_SCHEME_PATTERN,
)
TOKEN_PATTERN = re.compile(r"(?:sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9_]{20,})")
ABSOLUTE_PATH_PATTERN = re.compile(
    r"(?:~[/\\][^\s`'\"<>]+|/(?!(?i:goal)(?:\b|/))[^\s`'\"<>/]+"
    r"(?:/[^\s`'\"<>/]+)*|[A-Za-z]:\\[^\s`'\"<>]+)"
)
REMOTE_PATTERN = re.compile(
    r"(?:https?|ssh|git)://[^\s`'\"<>]+|[\w.+-]+@[\w.-]+:[^\s`'\"<>]+"
)
ENV_PATTERN = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\s*=\s*[^\s`'\"<>]+")
ENV_NAME_PATTERN = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b")
PRIVATE_MARKER_PATTERN = re.compile(r"\blocal-private\b", re.IGNORECASE)
ROUTING_TASK_FIELDS = {"kind", "state", "intent", "utterance"}
FINDINGS_TASK_FIELDS = {"kind", "spec", "diff", "context", "audience"}


def _quoted_segment_end(text: str, start: int) -> tuple[int, int]:
    quote = text[start]
    index = start + 1
    logical_length = 0
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text):
            if text[index + 1] == "\r" and index + 2 < len(text) and text[index + 2] == "\n":
                index += 3
            elif text[index + 1] in "\r\n":
                index += 2
            else:
                logical_length += 1
                index += 2
            continue
        if char == quote:
            return index + 1, logical_length
        if char not in "\r\n":
            logical_length += 1
        index += 1
    return len(text), logical_length


def _shell_expansion_end(text: str, start: int) -> int:
    stack = [")" if text.startswith("$(", start) else "}"]
    index = start + 2
    while index < len(text) and stack:
        char = text[index]
        if char == "\\" and index + 1 < len(text):
            if text[index + 1] == "\r" and index + 2 < len(text) and text[index + 2] == "\n":
                index += 3
            else:
                index += 2
            continue
        if char in "'\"`":
            index, _length = _quoted_segment_end(text, index)
            continue
        if text.startswith("$(", index):
            stack.append(")")
            index += 2
            continue
        if text.startswith("${", index):
            stack.append("}")
            index += 2
            continue
        opener = "(" if stack[-1] == ")" else "{"
        if char == opener:
            stack.append(stack[-1])
        elif char == stack[-1]:
            stack.pop()
        index += 1
    return index


def _secret_value_end(text: str, start: int) -> int | None:
    placeholder_end = start + len("<redacted>")
    if text.startswith("<redacted>", start) and (
        placeholder_end == len(text) or text[placeholder_end].isspace()
    ):
        return None

    index = start
    logical_length = 0
    has_expansion = False
    starts_quoted = (
        index < len(text) and text[index] in "'\"`"
    ) or text.startswith(("$'", '$"'), index)
    while index < len(text) and not text[index].isspace():
        char = text[index]
        if text.startswith(("$(", "${"), index):
            has_expansion = True
            index = _shell_expansion_end(text, index)
            continue
        if char == "$" and index + 1 < len(text) and text[index + 1] in "'\"":
            index += 1
            continue
        if char in "'\"`":
            index, segment_length = _quoted_segment_end(text, index)
            logical_length += segment_length
            continue
        if char == "\\" and index + 1 < len(text):
            if text[index + 1] == "\r" and index + 2 < len(text) and text[index + 2] == "\n":
                index += 3
            elif text[index + 1] == "\n":
                index += 2
            else:
                logical_length += 1
                index += 2
            continue
        logical_length += 1
        index += 1

    minimum = 4 if starts_quoted else 6
    return index if has_expansion or logical_length >= minimum else None


def _contains_secret_assignment(text: str) -> bool:
    cursor = 0
    while match := SECRET_KEY_PATTERN.search(text, cursor):
        end = _secret_value_end(text, match.end())
        if end is not None:
            return True
        cursor = match.end()
    return False


def _load_config(experiment: Path) -> ExperimentConfig:
    config_path = experiment / "config.json"
    if not config_path.is_file():
        raise ValueError(f"missing experiment config: {config_path}")
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("experiment config must be a JSON object")
    return ExperimentConfig.from_dict(data)


def _fixture_from_candidate(candidate: dict) -> dict:
    fixture = {
        "id": candidate.get("id"),
        "incident_id": candidate.get("incident_id"),
        "answerType": candidate.get("answerType"),
        "task": candidate.get("task"),
    }
    if candidate.get("answerType") == "routing-decision":
        fixture["expect"] = candidate.get("expect")
    elif candidate.get("answerType") == "findings-recall":
        fixture["answer"] = candidate.get("answer")
    return fixture


def _string_fields(value, path: str = "fixture") -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, list):
        fields: list[tuple[str, str]] = []
        for index, item in enumerate(value):
            fields.extend(_string_fields(item, f"{path}[{index}]"))
        return fields
    if isinstance(value, dict):
        fields = []
        for index, (key, item) in enumerate(value.items()):
            fields.append((f"{path}.key[{index}]", str(key)))
            fields.extend(_string_fields(item, f"{path}.value[{index}]"))
        return fields
    return []


def _commit_safe_issues(fixture: dict) -> list[str]:
    problems: list[str] = []
    for field_path, text in _string_fields(fixture):
        reasons: list[str] = []
        if not text.strip():
            reasons.append("blank")
        if PLACEHOLDER_PATTERN.search(text):
            reasons.append("placeholder")
        if (
            _contains_secret_assignment(text)
            or TOKEN_PATTERN.search(text)
            or any(pattern.search(text) for pattern in CREDENTIAL_PATTERNS)
        ):
            reasons.append("secret")
        if ABSOLUTE_PATH_PATTERN.search(text):
            reasons.append("absolute-path")
        if REMOTE_PATTERN.search(text):
            reasons.append("remote")
        if ENV_PATTERN.search(text):
            reasons.append("environment")
        if ENV_NAME_PATTERN.search(text):
            reasons.append("environment-name")
        if PRIVATE_MARKER_PATTERN.search(text):
            reasons.append("private-marker")
        if reasons:
            problems.append(
                f"not commit-safe: {field_path} ({','.join(dict.fromkeys(reasons))})"
            )
    return problems


def _real_judge_issues(cfg: ExperimentConfig) -> list[str]:
    judge_model = (cfg.judge_model or "").strip()
    if not judge_model:
        return ["recall_judge requires non-empty judge_model"]
    if "mock" in judge_model.lower():
        return ["recall_judge judge_model must not be mock"]
    if judge_model in set(cfg.model_list):
        return ["recall_judge judge_model must be independent from model_list"]
    return []


def _nonblank_text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_candidate(candidate: dict, cfg: ExperimentConfig) -> list[str]:
    problems: list[str] = []
    fixture_id = candidate.get("id")
    if not isinstance(fixture_id, str) or not SAFE_FIXTURE_ID_PATTERN.fullmatch(
        fixture_id
    ):
        problems.append("id must be a safe fixture basename")
    if candidate.get("_source") != "cs-feedback":
        problems.append("_source must be cs-feedback")
    if candidate.get("_status") != "candidate":
        problems.append("_status must be candidate")
    if candidate.get("privacy") != "local-private":
        problems.append("privacy must be local-private")
    privacy_review = candidate.get("privacy_review")
    if not isinstance(privacy_review, dict):
        problems.append("privacy_review must be an object")
    elif privacy_review.get("status") != "approved":
        problems.append("privacy_review.status must be approved")
    promotion_blockers = candidate.get("promotion_blockers")
    if not isinstance(promotion_blockers, list):
        problems.append("promotion_blockers must be an array")
    elif not all(isinstance(item, str) for item in promotion_blockers):
        problems.append("promotion_blockers entries must be strings")
    elif promotion_blockers:
        problems.append("promotion_blockers must be empty")
    quality = candidate.get("quality")
    if not isinstance(quality, dict):
        problems.append("quality must be an object")
    else:
        if quality.get("triage_ready") is not True:
            problems.append("quality.triage_ready must be true")
        if quality.get("regression_ready") is not True:
            problems.append("quality.regression_ready must be true")
        missing_fields = quality.get("missing_fields")
        if not isinstance(missing_fields, list) or not all(
            isinstance(item, str) for item in missing_fields
        ):
            problems.append("quality.missing_fields must be an array of strings")
    incident_id = candidate.get("incident_id")
    if not _nonblank_text(incident_id):
        problems.append("incident_id must be selected")
    if "regression" not in cfg.fixture_classes:
        problems.append("experiment config must enable the regression fixture class")

    target_skill_value = candidate.get("target_skill")
    if not _nonblank_text(target_skill_value):
        problems.append("target_skill must be a non-empty string")
        target_skill = "unknown"
    else:
        target_skill = target_skill_value
    if cfg.skill_under_test != target_skill:
        problems.append(
            f"candidate target_skill={target_skill} does not match config skill_under_test={cfg.skill_under_test}"
        )
    profile = candidate.get("_profile")
    answer_type = candidate.get("answerType")
    if not isinstance(profile, str):
        problems.append("_profile must be a string")
    if not isinstance(answer_type, str):
        problems.append("answerType must be a string")
    if profile != answer_type:
        problems.append("_profile must match answerType")
    incident_kind_value = candidate.get("incident_kind")
    if not _nonblank_text(incident_kind_value):
        problems.append("incident_kind must be a non-empty string")
        incident_kind = "unknown"
    else:
        incident_kind = incident_kind_value
    task_value = candidate.get("task")
    if not isinstance(task_value, dict):
        problems.append("task must be an object")
        task = {}
    else:
        task = task_value

    if profile == "routing-decision":
        if set(task) - ROUTING_TASK_FIELDS:
            problems.append("routing task contains unsupported fields")
        if incident_kind not in ROUTING_INCIDENT_KINDS:
            problems.append("routing-decision incident_kind is incompatible")
        if "routing_decision" not in cfg.scorers:
            problems.append("routing-decision candidate requires routing_decision scorer")
        if task.get("kind") != "routing":
            problems.append("routing candidate task.kind must be routing")
        for key in ("state", "intent"):
            if key in task and not isinstance(task[key], dict):
                problems.append(f"routing task.{key} must be an object")
        if "utterance" in task and not isinstance(task["utterance"], str):
            problems.append("routing task.utterance must be a string")
        if not (
            (isinstance(task.get("state"), dict) and bool(task["state"]))
            or (isinstance(task.get("intent"), dict) and bool(task["intent"]))
            or _nonblank_text(task.get("utterance"))
        ):
            problems.append("routing candidate needs state, intent, or utterance")
        expect = candidate.get("expect")
        if not isinstance(expect, dict) or not _nonblank_text(expect.get("result_type")):
            problems.append("routing candidate requires expect.result_type")
    elif profile == "findings-recall":
        if set(task) - FINDINGS_TASK_FIELDS:
            problems.append("findings-recall task contains unsupported fields")
        if incident_kind not in FINDINGS_INCIDENT_KINDS:
            problems.append("findings-recall incident_kind is incompatible")
        if "recall_judge" not in cfg.scorers:
            problems.append("findings-recall candidate requires recall_judge scorer")
        else:
            problems.extend(_real_judge_issues(cfg))
        kind_value = task.get("kind")
        if not isinstance(kind_value, str):
            problems.append("findings-recall task.kind must be a string")
            kind = ""
        else:
            kind = kind_value
        expected_kind = TASK_KIND_BY_TARGET.get(target_skill)
        if not expected_kind or kind != expected_kind:
            problems.append("findings-recall task.kind is incompatible with target_skill")
        for key in ("spec", "diff", "context", "audience"):
            if key in task and not isinstance(task[key], str):
                problems.append(f"findings-recall task.{key} must be a string")
        if kind in {"review", "audit"} and not _nonblank_text(task.get("diff")):
            problems.append(f"{kind} candidate requires diff")
        if kind == "fix" and (
            not _nonblank_text(task.get("spec")) or not _nonblank_text(task.get("diff"))
        ):
            problems.append("fix candidate requires spec and diff")
        if kind == "design" and not _nonblank_text(task.get("spec")):
            problems.append("design candidate requires spec")
        if kind == "docs" and (
            not _nonblank_text(task.get("spec")) or not _nonblank_text(task.get("diff"))
        ):
            problems.append("docs candidate requires spec and diff")
        if kind in {"design", "docs"} and not any(
            harness not in MOCK_HARNESSES for harness in cfg.harnesses
        ):
            problems.append(f"{kind} candidate requires a non-mock harness")
        answer = candidate.get("answer")
        if not isinstance(answer, list) or not answer or not all(
            isinstance(item, str) and item.strip() for item in answer
        ):
            problems.append("findings-recall candidate requires non-empty answer")
    else:
        problems.append(f"unsupported profile: {profile}")

    fixture = _fixture_from_candidate(candidate)
    problems.extend(validate_fixture_dict(fixture))
    if not problems:
        try:
            fixture_model = Fixture.from_dict(fixture)
            prompt = build_prompt(fixture_model, "# validation skill snapshot")
            if not prompt.strip():
                problems.append("buildPrompt returned empty output")
        except (AttributeError, TypeError, ValueError) as exc:
            problems.append(f"fixture/buildPrompt validation failed: {exc}")
    problems.extend(_commit_safe_issues(fixture))
    return list(dict.fromkeys(problems))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="promote cs-feedback candidate to experiment fixture"
    )
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--experiment", required=True)
    args = parser.parse_args(argv)

    candidate_path = Path(args.candidate).expanduser()
    experiment = Path(args.experiment).expanduser()
    try:
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        if not isinstance(candidate, dict):
            raise ValueError("candidate must be a JSON object")
        cfg = _load_config(experiment)
        problems = _validate_candidate(candidate, cfg)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"promotion blocked: {exc}", file=sys.stderr)
        return 2
    if problems:
        for problem in problems:
            print(f"promotion blocked: {problem}", file=sys.stderr)
        return 2

    fixture = _fixture_from_candidate(candidate)
    target_dir = experiment / "fixtures/regression"
    target = target_dir / f"{fixture['id']}.json"
    if target.resolve().parent != target_dir.resolve():
        print("promotion blocked: fixture target escapes regression directory", file=sys.stderr)
        return 2
    text = json.dumps(fixture, ensure_ascii=False, indent=2) + "\n"
    if target.is_file():
        if target.read_text(encoding="utf-8") == text:
            print(f"feedback fixture already promoted -> {target}")
            return 0
        print(f"promotion blocked: refusing to overwrite different fixture {target}", file=sys.stderr)
        return 2
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(target)
    print(f"promoted feedback fixture -> {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
