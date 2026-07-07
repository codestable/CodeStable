#!/usr/bin/env python3
"""e2e 场景工作目录准备：build seed repo + 注入 bug。

由 runner.py 在 with tempfile.TemporaryDirectory 块内调用，保持 runner 薄。
seed 仓库 build 完成后，harness 以 <tmp>/repo 作为工作目录执行。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True


def prepare_e2e_workdir(fixture, tmp: str, exp_dir: Path) -> Path:
    """构建 seed 仓库 + 注入 bug，返回 repo 目录路径。

    步骤：
    1. python3 experiments/seeds/<seed>/build-seed.py --out <tmp>/repo
    2. 若 <exp_dir>/bugs/<bug_id>/inject.py 存在，执行 python3 inject.py <repo>
    """
    scenario = (fixture.raw or {}).get("scenario") or {}
    seed = scenario["seed"]
    bug_id = scenario["bug_id"]

    repo = Path(tmp) / "repo"
    build_script = Path("experiments") / "seeds" / seed / "build-seed.py"

    result = subprocess.run(
        [sys.executable, str(build_script), "--out", str(repo)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"build-seed.py 失败 (seed={seed}):\n{result.stderr[:500]}"
        )

    inject_script = exp_dir / "bugs" / bug_id / "inject.py"
    if inject_script.exists():
        result2 = subprocess.run(
            [sys.executable, str(inject_script), str(repo)],
            capture_output=True, text=True,
        )
        if result2.returncode != 0:
            raise RuntimeError(
                f"inject.py 失败 (bug_id={bug_id}):\n{result2.stderr[:500]}"
            )

    return repo
