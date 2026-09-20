import hashlib
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "server"))
import regions

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

ex = data.get("exemplar")
if ex:
    for scene, cfg in ex["scenes"].items():
        assert cfg["labels"] == regions.labels(cfg["n"]), f"{scene}: label set"
        img = os.path.join(ROOT, "data", "scenes", f"{scene}.jpg")
        assert os.path.isfile(img), f"missing scene image: {scene}"
        for channel, refs in cfg["channels"].items():
            for name, r in refs.items():
                ref_img = os.path.join(ROOT, "data", "refs", f"{name}.jpg")
                assert os.path.isfile(ref_img), f"missing reference image: {name}"
                assert set(r["probs"]) == set(cfg["labels"]), f"{scene}/{channel}/{name}: regions"
                assert set(r["cells"]) <= set(cfg["labels"]), f"{scene}/{channel}/{name}: cells"
    print(f"exemplar: {len(ex['scenes'])} scenes, "
          f"{sum(len(c['channels']) for c in ex['scenes'].values())} channel runs")

page = open(os.path.join(ROOT, "index.html")).read()
m = re.search(r'src="data/results\.js\?v=([0-9a-f]+)"', page)
assert m, "page must load the cached results with a version stamp"
stamp = hashlib.sha1(json.dumps(data).encode()).hexdigest()[:8]
assert m.group(1) == stamp, (
    f"page asks for results.js?v={m.group(1)} but the data hashes to {stamp}; "
    "run scripts/build_results.py"
)
if ex:
    assert 'id="match"' in page, "page has exemplar data but no match view"
print(f"ok: {len(frames)} frames, {len(data['modes'])} modes, {data['n']}x{data['n']} grid")
