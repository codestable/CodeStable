#!/usr/bin/env python3

from pathlib import Path
import sys

EXPERIMENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXPERIMENT))
from _asset_mutations import apply_preflight  # noqa: E402

apply_preflight(Path(sys.argv[1]).resolve(), "display", "golden")
