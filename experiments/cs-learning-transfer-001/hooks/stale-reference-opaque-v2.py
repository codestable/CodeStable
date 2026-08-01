#!/usr/bin/env python3

from pathlib import Path
import sys

EXPERIMENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXPERIMENT))

from _asset_mutations import apply_stale_reference_policy  # noqa: E402


if __name__ == "__main__":
    apply_stale_reference_policy(Path(sys.argv[1]).resolve())
