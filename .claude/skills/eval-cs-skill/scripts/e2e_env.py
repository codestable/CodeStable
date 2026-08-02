#!/usr/bin/env python3
"""e2e 场景工作目录准备：build seed repo + 注入 bug。

由 runner.py 在 with tempfile.TemporaryDirectory 块内调用，保持 runner 薄。
seed 仓库 build 完成后，harness 以 <tmp>/repo 作为工作目录执行。
"""

from __future__ import annotations

import subprocess
import sys
import hashlib
import fnmatch
import os
import re
import shutil
import tempfile
from pathlib import Path

from _model import is_safe_slug

sys.dont_write_bytecode = True


_MANIFEST_IGNORED_PARTS = {"__pycache__", ".pytest_cache"}
_UNSAFE_GIT_CONTROL_PATHS = (
    "config.worktree",
    "commondir",
    "objects/info/alternates",
    "objects/info/http-alternates",
)
_SAFE_HOST_ENV_KEYS = ("PATH", "LANG", "LC_ALL", "SYSTEMROOT")


def isolated_subprocess_env(runtime: Path, *, pythonpath: Path | None = None) -> dict[str, str]:
    """Build a minimal deterministic-process environment without host credentials or injection."""
    home = runtime / "home"
    tmpdir = runtime / "tmp"
    home.mkdir(parents=True, exist_ok=True)
    tmpdir.mkdir(parents=True, exist_ok=True)
    env = {key: os.environ[key] for key in _SAFE_HOST_ENV_KEYS if key in os.environ}
    env.setdefault("PATH", os.defpath)
    env.update({
        "HOME": str(home),
        "TMPDIR": str(tmpdir),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "GIT_CONFIG_COUNT": "0",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
    })
    if pythonpath is not None:
        env["PYTHONPATH"] = str(pythonpath.resolve())
    return env


def reject_repo_symlinks(repo: Path) -> None:
    """实验 repo 禁止 symlink，避免 manifest/copy 越过 cell 边界。"""
    for path in repo.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"learning-transfer repo 禁止 symlink: {path.relative_to(repo)}")


def repo_manifest(repo: Path) -> dict[str, str]:
    """返回业务可见文件的相对路径→SHA-256；忽略 VCS 与测试缓存噪音。"""
    reject_repo_symlinks(repo)
    manifest: dict[str, str] = {}
    for path in sorted(repo.rglob("*")):
        relative = path.relative_to(repo)
        ignored = (
            relative.parts[0] == ".git"
            or _MANIFEST_IGNORED_PARTS & set(relative.parts)
        )
        if not path.is_file() or ignored:
            continue
        manifest[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return manifest


def _hash_optional_file(path: Path) -> str | None:
    if not path.exists():
        return None
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"git control path 不是普通文件: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hash_tree(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    manifest: dict[str, str] = {}
    for child in sorted(path.rglob("*")):
        if child.is_symlink():
            raise ValueError(f"git hooks 禁止 symlink: {child}")
        if child.is_file():
            mode = child.stat().st_mode & 0o777
            digest = hashlib.sha256(child.read_bytes()).hexdigest()
            manifest[child.relative_to(path).as_posix()] = f"{mode:o}:{digest}"
    return manifest


def _git_output(repo: Path, *args: str) -> str:
    try:
        with tempfile.TemporaryDirectory(prefix="cs-eval-git-", dir=repo.parent) as tmp:
            result = subprocess.run(
                ["git", *args],
                cwd=repo,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
                env=_isolated_git_env(Path(tmp)),
            )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"git {' '.join(args)} 超时") from exc
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 失败: {result.stderr[-300:]}")
    return result.stdout.strip()


def _isolated_git_env(runtime: Path) -> dict[str, str]:
    """只读取 cell 的 local config，不继承宿主仓库定位与配置注入。"""
    return isolated_subprocess_env(runtime)


def _local_config_has_includes(path: Path) -> bool:
    """不启动 Git，先从物理 local config 拒绝 include/includeIf。"""
    if not path.is_file() or path.is_symlink():
        return True
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError):
        return True
    section_pattern = re.compile(r"^\[\s*include(?:if\b[^]]*)?\s*]", re.IGNORECASE)
    dotted_pattern = re.compile(r"^include(?:if\.[^.]+)?\.path\s*=", re.IGNORECASE)
    for raw in lines:
        line = raw.lstrip()
        if not line or line.startswith(("#", ";")):
            continue
        if section_pattern.match(line) or dotted_pattern.match(line):
            return True
    return False


def repo_control_snapshot(repo: Path) -> dict[str, object]:
    """冻结 agent 不得改写的 Git HEAD、index 语义、local config 与 hooks。"""
    if repo.is_symlink():
        return {"repository": True, "safe": False, "git_layout": "repo-symlink"}
    repo_root = repo.resolve()
    physical_git_dir = repo_root / ".git"
    if physical_git_dir.is_symlink():
        return {
            "repository": True,
            "safe": False,
            "git_layout": hashlib.sha256(str(physical_git_dir).encode("utf-8")).hexdigest(),
        }
    if not physical_git_dir.exists():
        return {"repository": False, "safe": True}
    if not physical_git_dir.is_dir():
        return {
            "repository": True,
            "safe": False,
            "git_layout": hashlib.sha256(str(physical_git_dir).encode("utf-8")).hexdigest(),
        }

    config_file = physical_git_dir / "config"
    try:
        local_config = _hash_optional_file(config_file)
    except ValueError:
        local_config = None
    if local_config is None or _local_config_has_includes(config_file):
        return {
            "repository": True,
            "safe": False,
            "local_config": local_config,
        }
    unsafe_control_paths = [
        relative
        for relative in _UNSAFE_GIT_CONTROL_PATHS
        if (physical_git_dir / relative).exists()
        or (physical_git_dir / relative).is_symlink()
    ]
    if unsafe_control_paths:
        return {
            "repository": True,
            "safe": False,
            "local_config": local_config,
            "unsafe_control_paths": unsafe_control_paths,
        }

    git_dir = Path(_git_output(repo, "rev-parse", "--absolute-git-dir")).resolve()
    if git_dir != physical_git_dir.resolve():
        return {
            "repository": True,
            "safe": False,
            "external_git_dir": hashlib.sha256(str(git_dir).encode("utf-8")).hexdigest(),
            "local_config": local_config,
        }

    def git_path(name: str) -> tuple[Path | None, str]:
        raw = _git_output(repo, "rev-parse", "--git-path", name)
        path = Path(raw)
        resolved = (path if path.is_absolute() else repo / path).resolve()
        safe = False
        for base in (repo_root, git_dir):
            try:
                resolved.relative_to(base)
                safe = True
                break
            except ValueError:
                continue
        return (resolved if safe else None), hashlib.sha256(raw.encode("utf-8")).hexdigest()

    index_path, index_location = git_path("index")
    config_path, config_location = git_path("config")
    hooks_path, hooks_location = git_path("hooks")
    control_paths_safe = (
        index_path is not None
        and config_path is not None
        and hooks_path is not None
        and config_path == config_file.resolve()
    )

    return {
        "repository": True,
        "safe": control_paths_safe,
        "head": _git_output(repo, "rev-parse", "--verify", "HEAD"),
        "head_ref": _git_output(repo, "rev-parse", "--symbolic-full-name", "HEAD"),
        "index_location": index_location,
        # Git 的只读命令可刷新 index stat cache；只冻结 staged entries 与 index flags。
        "index": (
            hashlib.sha256(
                _git_output(repo, "ls-files", "--stage", "-v", "-z").encode("utf-8")
            ).hexdigest()
            if index_path is not None
            else None
        ),
        "config_location": config_location,
        "local_config": local_config,
        "hooks_location": hooks_location,
        "hooks": _hash_tree(hooks_path) if hooks_path is not None else None,
    }


def repo_control_unchanged(before: dict[str, object], after: dict[str, object]) -> bool:
    """只有初始/最终控制面都位于 cell 内且字节相同才算未改写。"""
    return before.get("safe") is True and after == before


def copy_repo(source: Path, destination: Path) -> Path:
    """完整复制一个 repo；manifest 调用方负责验证业务内容完全相同。"""
    reject_repo_symlinks(source)
    shutil.copytree(source, destination, symlinks=True)
    reject_repo_symlinks(destination)
    return destination


def changed_paths(before: dict[str, str], after: dict[str, str]) -> set[str]:
    """比较两个 manifest，包含新增、修改和删除路径。"""
    return {
        path for path in set(before) | set(after)
        if before.get(path) != after.get(path)
    }


def paths_match_allowlist(paths: set[str], patterns: list[str]) -> bool:
    """所有变化都必须命中至少一个声明的相对路径 glob。"""
    return all(any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns) for path in paths)


def build_seed_repo(seed: str, destination: Path, root: Path) -> Path:
    """用 tracked seed builder 构建一个全新的独立仓库。"""
    if not is_safe_slug(seed):
        raise ValueError(f"seed 必须是安全 slug: {seed!r}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    seed_root = (root / "experiments" / "seeds").resolve()
    build_script = (seed_root / seed / "build-seed.py").resolve()
    try:
        build_script.relative_to(seed_root)
    except ValueError as exc:
        raise ValueError(f"seed builder 越过 experiments/seeds: {seed!r}") from exc
    if not build_script.is_file() or (seed_root / seed / "build-seed.py").is_symlink():
        raise ValueError(f"seed builder 不存在或为 symlink: {seed!r}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="cs-eval-seed-", dir=destination.parent) as tmp:
            result = subprocess.run(
                [sys.executable, "-I", "-B", str(build_script), "--out", str(destination)],
                cwd=root,
                env=isolated_subprocess_env(Path(tmp), pythonpath=root),
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"build-seed.py 超时 (seed={seed})") from exc
    if result.returncode != 0:
        raise RuntimeError(f"build-seed.py 失败 (seed={seed}):\n{result.stderr[-500:]}")
    return destination


def prepare_e2e_workdir(fixture, tmp: str, exp_dir: Path) -> Path:
    """构建 seed 仓库 + 注入 bug，返回 repo 目录路径。

    步骤：
    1. python3 experiments/seeds/<seed>/build-seed.py --out <tmp>/repo
    2. 若 <exp_dir>/bugs/<bug_id>/inject.py 存在，执行 python3 inject.py <repo>
    """
    scenario = (fixture.raw or {}).get("scenario") or {}
    seed = scenario["seed"]
    bug_id = scenario.get("bug_id")  # feature 场景无 bug 注入

    repo = Path(tmp) / "repo"
    root = Path.cwd()
    build_seed_repo(seed, repo, root)

    inject_script = (exp_dir / "bugs" / bug_id / "inject.py") if bug_id else None
    if inject_script and inject_script.exists():
        with tempfile.TemporaryDirectory(prefix="cs-eval-inject-", dir=repo.parent) as tmp:
            result2 = subprocess.run(
                [sys.executable, "-I", "-B", str(inject_script), str(repo)],
                cwd=root,
                env=isolated_subprocess_env(Path(tmp), pythonpath=root),
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )
        if result2.returncode != 0:
            raise RuntimeError(
                f"inject.py 失败 (bug_id={bug_id}):\n{result2.stderr[:500]}"
            )

    return repo
