"""Fail the build if the page and the cached results disagree."""
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "server"))
import regions  # noqa: E402

src = open(os.path.join(ROOT, "data", "results.js")).read()
data = json.loads(re.match(r"\s*window\.RESULTS\s*=\s*(\{.*\});\s*$", src, re.S).group(1))

assert data["labels"] == regions.labels(data["n"]), "label set does not match the grid"
frames = data["frames"]
for mode, maps in data["modes"].items():
    assert len(maps) == len(frames), f"{mode}: {len(maps)} maps for {len(frames)} frames"
    for m in maps:
        assert set(m) == set(data["labels"]), f"{mode}: region set mismatch"
assert len(data["times"]) == len(frames), "timing count does not match frames"
missing = [f for f in frames if not os.path.isfile(os.path.join(ROOT, "data", "frames", f))]
assert not missing, f"missing frame files: {missing[:5]}"

page = open(os.path.join(ROOT, "index.html")).read()
assert 'src="data/results.js"' in page, "page does not load the cached results"
print(f"ok: {len(frames)} frames, {len(data['modes'])} modes, {data['n']}x{data['n']} grid")
