from __future__ import annotations

import os
import sys

import pytest


sys.dont_write_bytecode = True
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-real-cli",
        action="store_true",
        default=False,
        help="运行会启动本机 Claude/Codex CLI 的显式 E2E 测试",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "real_cli: 需要显式 --run-real-cli 才会启动本机 Claude/Codex CLI",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-real-cli"):
        return
    skip_real_cli = pytest.mark.skip(
        reason="需要显式 --run-real-cli；默认测试不得启动本机 Claude/Codex CLI",
    )
    for item in items:
        if "real_cli" in item.keywords:
            item.add_marker(skip_real_cli)
