"""Merge a freshly-built local repo into the published snapshot repo.

Usage: merge-snapshot.py <local_repo_dir> <remote_repo_dir>

  local_repo_dir   the `repo/` produced by create-repo.py for this run
                   (contains index.min.json + apk/ + icon/)
  remote_repo_dir  the gh-pages checkout to publish into

Behaviour:
  * Fetches the official Keiyoushi index and DROPS any just-built extension
    whose upstream versionCode is >= ours (upstream has caught up -> let the
    official repo serve it; "override on merge").
  * Merges the kept extensions into the published index (replacing same pkg,
    adding new ones), copies their apk/icon, and prunes any orphaned files.
  * Only writes index.min.json (the format Tachimanga / Mihon consume); URLs
    stay relative so the repo is portable to any host (GitHub Pages here).
"""

import json
import shutil
import sys
import urllib.request
from pathlib import Path

OFFICIAL_INDEX_URL = (
    "https://raw.githubusercontent.com/keiyoushi/extensions/repo/index.min.json"
)

LOCAL = Path(sys.argv[1])
REMOTE = Path(sys.argv[2])

(REMOTE / "apk").mkdir(parents=True, exist_ok=True)
(REMOTE / "icon").mkdir(parents=True, exist_ok=True)


def load_index(path: Path) -> list:
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


remote_index = load_index(REMOTE / "index.min.json")
local_index = load_index(LOCAL / "index.min.json")

# Official upstream versions, for the "override on merge" filter.
try:
    with urllib.request.urlopen(OFFICIAL_INDEX_URL, timeout=60) as resp:
        official = json.load(resp)
    official_code = {e["pkg"]: e["code"] for e in official}
except Exception as err:  # noqa: BLE001 - non-fatal, just skip the filter
    print(f"WARN: could not fetch official index ({err}); skipping override filter")
    official_code = {}

built_pkgs = {e["pkg"] for e in local_index}

kept, dropped = [], []
for entry in local_index:
    upstream = official_code.get(entry["pkg"])
    if upstream is not None and upstream >= entry["code"]:
        dropped.append(entry["pkg"])
    else:
        kept.append(entry)

# Rebuild the published index: keep everything previously published except the
# packages we (re)built this run, then add back the ones we're keeping.
merged_by_pkg = {e["pkg"]: e for e in remote_index if e["pkg"] not in built_pkgs}
for entry in kept:
    merged_by_pkg[entry["pkg"]] = entry
merged = sorted(merged_by_pkg.values(), key=lambda e: e["pkg"])

# Copy the kept apk + icon files into the published repo.
for entry in kept:
    shutil.copy(LOCAL / "apk" / entry["apk"], REMOTE / "apk" / entry["apk"])
    icon = f'{entry["pkg"]}.png'
    icon_src = LOCAL / "icon" / icon
    if icon_src.exists():
        shutil.copy(icon_src, REMOTE / "icon" / icon)

with (REMOTE / "index.min.json").open("w", encoding="utf-8") as f:
    json.dump(merged, f, ensure_ascii=False, separators=(",", ":"))

# Prune apk/icon files no longer referenced by the published index.
referenced_apk = {e["apk"] for e in merged}
referenced_icon = {f'{e["pkg"]}.png' for e in merged}
for f in (REMOTE / "apk").iterdir():
    if f.is_file() and f.name not in referenced_apk:
        f.unlink()
for f in (REMOTE / "icon").iterdir():
    if f.is_file() and f.name not in referenced_icon:
        f.unlink()

# Simple human-readable listing for manual downloads.
with (REMOTE / "index.html").open("w", encoding="utf-8") as f:
    f.write("<!DOCTYPE html>\n<meta charset='utf-8'>\n<title>snapshot apks</title>\n<pre>\n")
    for entry in merged:
        f.write(f'<a href="apk/{entry["apk"]}">{entry["name"]}</a> (v{entry["version"]})\n')
    f.write("</pre>\n")

print(f"kept ({len(kept)}): {sorted(e['pkg'] for e in kept)}")
print(f"dropped, upstream caught up ({len(dropped)}): {dropped}")
print(f"total published: {len(merged)}")
