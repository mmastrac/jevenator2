import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "server"))
import regions

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "data")
HALF = 2

base = json.load(open(os.path.join(DATA, "maps.json")))
COLS, ROWS = base.get("cols", 5), base.get("rows", 5)
temporal = json.load(open(os.path.join(DATA, "temporal.json")))
names = sorted(base["maps"])
single = [base["maps"][n] for n in names]

payload = {
    "cols": COLS,
    "rows": ROWS,
    "labels": regions.labels(COLS, ROWS),
    "target": "a boy with light blond hair",
    "frames": [n.replace(".png", ".jpg") for n in names],
    "times": base["times"],
    "modes": {
        "single": single,
        "averaged": [regions.smooth(single, i, HALF, COLS, ROWS) for i in range(len(single))],
        "prev": [temporal["B_true"][n] for n in names],
        "wrong": [temporal["C_wrong"][n] for n in names],
    },
}
tracks_path = os.path.join(DATA, "tracks.json")
if os.path.isfile(tracks_path):
    tr = json.load(open(tracks_path))
    assert (tr["cols"], tr["rows"]) == (COLS, ROWS), "tracks were scanned on a different grid"
    payload["refs"] = {
        name: {"ms": t["ms"],
               "modes": {"single": t["maps"],
                         "averaged": [regions.smooth(t["maps"], i, HALF, COLS, ROWS)
                                      for i in range(len(t["maps"]))]}}
        for name, t in tr["tracks"].items()
    }
    payload["ref_channel"] = tr["channel"]
    ex_path = os.path.join(DATA, "exemplar.json")
    if os.path.isfile(ex_path):
        ex = json.load(open(ex_path))
        desc = ex["scenes"]["night"].get("descriptions", {})
        for name in payload["refs"]:
            payload["refs"][name]["description"] = desc.get(name, "")

body = json.dumps(payload)
stamp = hashlib.sha1(body.encode()).hexdigest()[:8]

out = os.path.join(DATA, "results.js")
with open(out, "w") as f:
    f.write("window.RESULTS = " + body + ";\n")

index = os.path.join(ROOT, "index.html")
page = open(index).read()
page, hits = re.subn(r'src="data/results\.js(?:\?v=[0-9a-f]+)?"',
                     f'src="data/results.js?v={stamp}"', page)
assert hits == 1, f"expected one results.js script tag, found {hits}"
open(index, "w").write(page)

print(f"{out}  {os.path.getsize(out) // 1024} KB  {len(names)} frames  v={stamp}")
