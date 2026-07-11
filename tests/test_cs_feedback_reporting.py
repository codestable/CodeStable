from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_SCRIPT = ROOT / "plugins/codestable/skills/cs-feedback/scripts/report_feedback_issue.py"


def load_reporter():
    spec = importlib.util.spec_from_file_location("report_feedback_issue_contract", REPORT_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


reporter = load_reporter()
privacy = sys.modules["feedback_privacy"]


def test_public_body_scanner_rejects_single_segment_path_and_env_name() -> None:
    reasons = reporter.public_body_private_reasons(
        "failed in /repo while reading API_TOKEN"
    )
    assert "absolute-path" in reasons
    assert "environment-name" in reasons
    assert "absolute-path" not in reporter.public_body_private_reasons(
        "run /goal for this feature"
    )


def test_public_body_scanner_handles_absolute_paths_with_spaces_end_to_end() -> None:
    cases = (
        (r"error at C:\Users\bob\secret plan.docx", ("plan.docx",)),
        (
            "/Users/alice/customer contracts/acme-pricing-2026.md",
            ("contracts", "acme-pricing-2026.md"),
        ),
        (
            "/Users/alice/Library/Application Support/CodeStable/session.json",
            ("Support", "CodeStable", "session.json"),
        ),
        (
            'cat "/Users/alice/acme merger notes.txt" done',
            ("merger", "notes.txt"),
        ),
        (
            "cat '/Users/alice/acme merger notes.txt' done",
            ("merger", "notes.txt"),
        ),
        (
            "cat `/Users/alice/acme merger notes.txt` done",
            ("merger", "notes.txt"),
        ),
        (
            'open "C:\\Users\\bob\\secret plan.docx" now',
            ("plan.docx",),
        ),
        ("see /Users/bob/my report.docx.", ("report.docx",)),
        ("see /Users/bob/my report.docx!", ("report.docx",)),
        ("see /Users/bob/my report.docx?", ("report.docx",)),
        ("see /Users/bob/my report.docx。", ("report.docx",)),
        ("see /Users/bob/my report.docx！", ("report.docx",)),
        ("see /Users/bob/my report.docx？", ("report.docx",)),
        (
            'see "/Users/bob/my report.docx." next',
            ("report.docx",),
        ),
        (
            "请看 /Users/alice/acme 合并 计划.docx，其中第二节有问题",
            ("合并", "计划.docx"),
        ),
        (
            "路径是 /Users/alice/acme 合并 计划.docx。下一步继续",
            ("合并", "计划.docx"),
        ),
        (
            "（详见 /Users/alice/merger plan.docx）之后再说",
            ("merger", "plan.docx"),
        ),
        (
            "见 /Users/alice/plan file.docx；继续",
            ("plan", "file.docx"),
        ),
        (
            "见“/Users/alice/acme 合并 计划.docx”，继续",
            ("合并", "计划.docx"),
        ),
        (
            "见 /Users/alice/plan long.presentation，继续",
            ("long.presentation",),
        ),
        (
            "见 /Users/alice/客户 合同.文档，继续",
            ("合同.文档",),
        ),
        (
            "请看 /Users/alice/acme 合并 计划.docx…其中有问题",
            ("合并", "计划.docx"),
        ),
        (
            "请看 /Users/alice/acme 合并 计划.docx——其中有问题",
            ("合并", "计划.docx"),
        ),
        (
            "请看 /Users/alice/acme 合并 计划.docx（内含预算）",
            ("合并", "计划.docx"),
        ),
        (
            "see /Users/alice/acme merger plan.docx(v2)",
            ("merger", "plan.docx"),
        ),
        (
            "请看 /Users/alice/acme 合并 计划.docx·补充",
            ("合并", "计划.docx"),
        ),
        (
            "请看 /Users/alice/acme 合并 计划.docx～补充",
            ("合并", "计划.docx"),
        ),
        (
            "请看 /Users/alice/acme 合并 计划.docx“重点”",
            ("合并", "计划.docx"),
        ),
        (
            "/tmp/x my report.docx 之后继续",
            ("my", "report.docx"),
        ),
        (
            r"open C:\Program Files\CodeStable\session.json",
            ("Files", "CodeStable", "session.json"),
        ),
        (
            "/Users/alice/项目 文档/计划.docx",
            ("文档", "计划.docx"),
        ),
        ("/tmp/x 合同.docx", ("合同.docx",)),
    )
    for raw, forbidden_parts in cases:
        assert "absolute-path" in reporter.public_body_private_reasons(raw)
        sanitized = privacy.public_redact(raw)
        assert all(part not in sanitized for part in forbidden_parts)
        assert reporter.public_body_private_reasons(sanitized) == []


def test_public_body_scanner_preserves_text_after_absolute_paths() -> None:
    cases = (
        (
            "报错发生在 /tmp/build，随后 agent 跳过了 review gate",
            "，随后 agent 跳过了 review gate",
        ),
        (
            "/Users/alice/acme，其中第二节有问题",
            "，其中第二节有问题",
        ),
        (
            "cs-feat 在 /tmp/repo 之后 应该 先跑 design-review.md 再实现",
            "之后 应该 先跑 design-review.md 再实现",
        ),
        (
            "/tmp/a 运行 失败.详情如下：日志已附",
            "运行 失败.详情如下：日志已附",
        ),
        (
            "/tmp/build 失败 详见 3.2 节",
            "失败 详见 3.2 节",
        ),
        (
            "agent 在 /tmp/repo 没有读 .codestable/attention.md 就开工",
            "没有读 .codestable/attention.md 就开工",
        ),
        (
            "/tmp/build 失败 详见 docs/report.md",
            "失败 详见 docs/report.md",
        ),
        (
            "/tmp/app v1.2.3 crashed",
            "v1.2.3 crashed",
        ),
        (
            "/tmp/build 失败.详情如下 请看日志",
            "失败.详情如下 请看日志",
        ),
        (
            "/Users/a/b/c 详见 3.2 节",
            "详见 3.2 节",
        ),
        (
            "cs-feat 在 /tmp/repo 没生成.codestable/design.md",
            "没生成.codestable/design.md",
        ),
        (
            "报错在 /tmp/repo 后写到了build/output.json",
            "后写到了build/output.json",
        ),
        (
            "/tmp/x 输出在logs/a.txt 又读了docs/b.md 然后停了",
            "输出在logs/a.txt 又读了docs/b.md 然后停了",
        ),
    )
    for raw, expected_text in cases:
        assert "absolute-path" in reporter.public_body_private_reasons(raw)
        sanitized = privacy.public_redact(raw, limit=4000)
        assert expected_text in sanitized
        assert reporter.public_body_private_reasons(sanitized) == []


def test_public_body_scanner_rejects_nested_and_unbounded_tool_json() -> None:
    nested = '{"patch":"def f() { return {} }","note":"private logic"}'
    oversized = '{"note":"private prefix","payload":"' + ("x" * 2500) + '"}'

    assert "raw-json" in reporter.public_body_private_reasons(nested)
    assert "raw-json" in reporter.public_body_private_reasons(oversized)


def test_public_body_scanner_rejects_six_and_seven_character_explicit_secrets() -> None:
    for raw in ("password=hunter2", "authorization=abcdefg", '"token":"secret"'):
        assert "secret" in reporter.public_body_private_reasons(raw)


def test_public_body_scanner_rejects_special_and_quoted_secret_values() -> None:
    cases = (
        ("password=p@ssw0rd!123", ("p@ssw0rd!123",)),
        ('password: "correct horse battery staple"', ("correct", "horse", "battery", "staple")),
        ('export password="s3cr3tv@lue"', ("s3cr3tv@lue", "@lue")),
        ('token = "abc def ghi jkl"', ("abc", "def", "ghi", "jkl")),
        ("password=abc<def>ghi", ("abc<def>ghi",)),
        ("password=`s3cr3tv@l!`", ("s3cr3tv@l!",)),
        ("password：hunter22!", ("hunter22!",)),
        ("token＝abc<def>ghi", ("abc<def>ghi",)),
        ('password="s3cr3tv@lue', ("s3cr3tv@lue",)),
        ("token='unterminated secret value", ("unterminated", "secret", "value")),
        (r"password=secret\ pass", (r"secret\ pass", " pass")),
        ("password：`abc<def>ghi`", ("abc<def>ghi",)),
    )
    for raw, forbidden_parts in cases:
        assert "secret" in reporter.public_body_private_reasons(raw)
        sanitized = privacy.public_redact(raw)
        assert all(part not in sanitized for part in forbidden_parts)
        assert reporter.public_body_private_reasons(sanitized) == []


def test_public_body_scanner_rejects_shell_segmented_secret_values() -> None:
    cases = (
        ("password=abc'def'ghi", ("abc", "def", "ghi")),
        ('password=abc"def"ghi', ("abc", "def", "ghi")),
        ("password=abc`def`ghi", ("abc", "def", "ghi")),
        ("password=abc\\\ndef", ("abc", "def")),
        ("password=$'abcd'", ("abcd",)),
        ("password=$(printf secretvalue)", ("secretvalue",)),
    )
    for raw, forbidden_parts in cases:
        assert "secret" in reporter.public_body_private_reasons(raw)
        sanitized = privacy.public_redact(raw)
        assert all(part not in sanitized for part in forbidden_parts)
        assert reporter.public_body_private_reasons(sanitized) == []


def test_public_body_scanner_rejects_multiline_shell_secret_values() -> None:
    cases = (
        ('password="abcd\nsecretvalue"', ("abcd", "secretvalue")),
        ("password='ab\r\ncdefgh'", ("ab", "cdefgh")),
        ("password=$'a\nbcdefgh'", ("bcdefgh",)),
        ("password=$(\nprintf secretvalue\n)", ("printf", "secretvalue")),
        ("password=${TOKEN:-\nsecretvalue\n}", ("secretvalue",)),
    )
    for raw, forbidden_parts in cases:
        assert "secret" in reporter.public_body_private_reasons(raw)
        sanitized = privacy.public_redact(raw, limit=4000)
        assert all(part not in sanitized for part in forbidden_parts)
        assert reporter.public_body_private_reasons(sanitized) == []


def test_public_body_scanner_accepts_sanitized_privacy_placeholders() -> None:
    for sanitized in (
        "password=<redacted>",
        "password：<redacted>",
        "<auth-credential>",
        "<user-credential>",
        "<local-path>",
        "<url>",
        "<env>",
    ):
        assert reporter.public_body_private_reasons(sanitized) == []


def test_public_body_scanner_rejects_http_auth_schemes_and_accepts_sanitized_text() -> None:
    cases = (
        ("Authorization: Basic dXNlcjpwYXNz", "dXNlcjpwYXNz"),
        ("authorization: bearer abc123def", "abc123def"),
        ("Proxy-Authorization=Basic cHJveHk6cGFzcw==", "cHJveHk6cGFzcw=="),
        ("Bearer standalone123", "standalone123"),
    )
    for raw, credential in cases:
        assert "secret" in reporter.public_body_private_reasons(raw)
        sanitized = privacy.public_redact(raw)
        assert credential not in sanitized
        assert reporter.public_body_private_reasons(sanitized) == []


def test_public_body_scanner_rejects_auth_headers_env_order_and_curl_userinfo() -> None:
    cases = (
        ("AUTHORIZATION=Basic dXNlcjpwYXNz", "dXNlcjpwYXNz"),
        ("HTTP_AUTHORIZATION=Basic aHR0cDpwYXNz", "aHR0cDpwYXNz"),
        ("Authorization: token ghp_short12", "ghp_short12"),
        (
            'Authorization: Digest username="u", response="6629fae49393a05397450978507c4ef1"',
            "6629fae49393a05397450978507c4ef1",
        ),
        ("curl -u deploy:password123 endpoint", "deploy:password123"),
    )
    for raw, credential in cases:
        assert "secret" in reporter.public_body_private_reasons(raw)
        sanitized = privacy.public_redact(raw)
        assert credential not in sanitized
        assert reporter.public_body_private_reasons(sanitized) == []


def test_reporter_falls_back_when_gh_is_missing(tmp_path: Path, monkeypatch) -> None:
    body = tmp_path / "github-issue.md"
    body.write_text("## Summary\n\ncs-feedback issue\n", encoding="utf-8")
    output = tmp_path / "result.json"
    monkeypatch.setattr(reporter.shutil, "which", lambda name: None)

    exit_code = reporter.main_with_args_for_test(
        [
            "--repo",
            "owner/repo",
            "--title",
            "Feedback: cs skill failed",
            "--body-file",
            str(body),
            "--json-output",
            str(output),
        ]
    )

    assert exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "manual"
    assert payload["reason"] == "gh not found"
    assert "gh issue create" in payload["command"]
    assert "'Feedback: cs skill failed'" in payload["command"]


def test_reporter_refuses_local_private_evidence(tmp_path: Path, monkeypatch) -> None:
    evidence = tmp_path / "evidence.json"
    evidence.write_text(
        json.dumps({"privacy": "local-private", "public_upload_allowed": False}),
        encoding="utf-8",
    )
    monkeypatch.setattr(reporter.shutil, "which", lambda name: None)

    try:
        reporter.main_with_args_for_test(
            [
                "--repo",
                "owner/repo",
                "--title",
                "Feedback: cs skill failed",
                "--body-file",
                str(evidence),
            ]
        )
    except SystemExit as exc:
        assert "refusing to upload local-private" in str(exc)
    else:
        raise AssertionError("expected reporter to reject evidence.json")


def test_reporter_requires_explicit_public_preview_confirmation(tmp_path: Path, monkeypatch) -> None:
    body = tmp_path / "github-issue.md"
    body.write_text("# Public issue\n\nSanitized summary.\n", encoding="utf-8")
    calls: list[list[str]] = []
    monkeypatch.setattr(reporter.shutil, "which", lambda _name: "/usr/local/bin/gh")

    def fake_run(command):
        calls.append(command)
        raise AssertionError("gh must not run before explicit public-preview confirmation")

    monkeypatch.setattr(reporter, "run_with_proxy_retry", fake_run)
    assert (
        reporter.main_with_args_for_test(
            ["--repo", "owner/repo", "--title", "feedback", "--body-file", str(body)]
        )
        == 0
    )
    assert calls == []


def test_reporter_confirmed_preview_calls_only_auth_and_issue_create(tmp_path: Path, monkeypatch) -> None:
    body = tmp_path / "github-issue.md"
    body.write_text("# Public issue\n\nSanitized summary.\n", encoding="utf-8")
    calls: list[list[str]] = []
    monkeypatch.setattr(reporter.shutil, "which", lambda _name: "/usr/local/bin/gh")

    def fake_run(command):
        calls.append(command)
        stdout = "https://github.com/owner/repo/issues/1\n" if "create" in command else ""
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr=""), None

    monkeypatch.setattr(reporter, "run_with_proxy_retry", fake_run)
    assert (
        reporter.main_with_args_for_test(
            [
                "--repo",
                "owner/repo",
                "--title",
                "feedback",
                "--body-file",
                str(body),
                "--confirm-public-preview",
            ]
        )
        == 0
    )
    assert len(calls) == 2
    assert calls[0][-2:] == ["auth", "status"]
    assert calls[1][1:3] == ["issue", "create"]


def test_reporter_rejects_private_content_even_after_confirmation(tmp_path: Path, monkeypatch) -> None:
    body = tmp_path / "github-issue.md"
    body.write_text("Private path: /Users/me/client/repo/secret.md\n", encoding="utf-8")
    calls: list[list[str]] = []
    monkeypatch.setattr(reporter.shutil, "which", lambda _name: "/usr/local/bin/gh")

    def fake_run(command):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr=""), None

    monkeypatch.setattr(reporter, "run_with_proxy_retry", fake_run)
    try:
        reporter.main_with_args_for_test(
            [
                "--repo",
                "owner/repo",
                "--title",
                "feedback",
                "--body-file",
                str(body),
                "--confirm-public-preview",
            ]
        )
    except SystemExit as exc:
        assert "public preview contains private content" in str(exc)
    else:
        raise AssertionError("expected private public-preview body to be rejected")
    assert calls == []


def test_reporter_rejects_private_title_even_after_confirmation(tmp_path: Path, monkeypatch) -> None:
    body = tmp_path / "github-issue.md"
    body.write_text("# Public issue\n\nSanitized summary.\n", encoding="utf-8")
    calls: list[list[str]] = []
    monkeypatch.setattr(reporter.shutil, "which", lambda _name: "/usr/local/bin/gh")

    def fake_run(command):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr=""), None

    monkeypatch.setattr(reporter, "run_with_proxy_retry", fake_run)
    try:
        reporter.main_with_args_for_test(
            [
                "--repo",
                "owner/repo",
                "--title",
                "fails in /Users/me/client-x",
                "--body-file",
                str(body),
                "--confirm-public-preview",
            ]
        )
    except SystemExit as exc:
        assert "issue title contains private content" in str(exc)
    else:
        raise AssertionError("expected private issue title to be rejected")
    assert calls == []


def test_reporter_refuses_triage_and_regression_candidate_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(reporter.shutil, "which", lambda name: None)
    for name in ("triage.json", "regression-candidate.json"):
        private = tmp_path / name
        private.write_text(json.dumps({"privacy": "local-private"}), encoding="utf-8")
        try:
            reporter.main_with_args_for_test(
                ["--repo", "owner/repo", "--title", "x", "--body-file", str(private)]
            )
        except SystemExit as exc:
            assert "refusing to upload local-private" in str(exc)
        else:
            raise AssertionError(f"expected reporter to reject {name}")
