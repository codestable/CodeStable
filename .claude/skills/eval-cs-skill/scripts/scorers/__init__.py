"""scorer 包：import 即注册。加 scorer = 加一个模块并在此 import。"""

from __future__ import annotations

import importlib

from .base import applies, available, get_scorer  # noqa: F401

from . import planted_defect  # noqa: F401

# 后续阶段的 scorer；缺依赖不阻断确定性路径
for _mod in ("dod_gate", "llm_judge", "recall_judge", "routing_decision", "e2e_outcome"):
    try:
        importlib.import_module(f".{_mod}", __name__)
    except Exception:  # noqa: BLE001
        pass
