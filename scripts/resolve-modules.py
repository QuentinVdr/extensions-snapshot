"""Resolve the list of Gradle assemble tasks to build.

If MANUAL (the `extensions` workflow input) is set, build exactly those.
Otherwise fall back to MATRIX (output of the fork's generate-build-matrices.py,
i.e. the extensions changed vs upstream/main).

Accepted MANUAL token formats (space- or comma-separated):
  fr/raijinscans   fr.raijinscans   src/fr/raijinscans   :src:fr:raijinscans
"""

import json
import os
import re
from pathlib import Path

manual = os.environ.get("MANUAL", "").strip()
matrix = os.environ.get("MATRIX", "").strip()
src_root = Path(os.environ.get("FORK_DIR", "main")) / "src"


def to_module(token: str) -> str:
    normalized = token.strip().strip(":").replace(":", "/").replace(".", "/")
    parts = [p for p in normalized.split("/") if p and p != "src"]
    if len(parts) < 2:
        raise SystemExit(
            f"::error::Cannot parse extension '{token}'. Use lang/name, e.g. fr/raijinscans"
        )
    lang, name = parts[-2], parts[-1]
    if not (src_root / lang / name).is_dir():
        raise SystemExit(
            f"::error::Extension src/{lang}/{name} not found on this branch"
        )
    return f":src:{lang}:{name}:assembleRelease"


if manual:
    tokens = [t for t in re.split(r"[\s,]+", manual) if t.strip()]
    modules = [to_module(t) for t in tokens]
else:
    data = json.loads(matrix or "{}")
    modules = [m for chunk in data.get("chunk", []) for m in chunk["modules"]]

# de-duplicate while preserving order
print(" ".join(dict.fromkeys(modules)))
