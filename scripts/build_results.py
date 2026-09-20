import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "server"))
import regions

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "data")
N = 5
HALF = 2

base = json.load(open(os.path.join(DATA, "maps.json")))
temporal = json.load(open(os.path.join(DATA, "temporal.json")))
names = sorted(base["maps"])
single = [base["maps"][n] for n in names]

payload = {
    "n": N,
    "labels": regions.labels(N),
    "target": "a boy with light blond hair",
    "frames": [n.replace(".png", ".jpg") for n in names],
    "times": base["times"],
    "modes": {
        "single": single,
        "averaged": [regions.smooth(single, i, HALF, N) for i in range(len(single))],
        "prev": [temporal["B_true"][n] for n in names],
        "wrong": [temporal["C_wrong"][n] for n in names],
    },
}
exemplar_path = os.path.join(DATA, "exemplar.json")
if os.path.isfile(exemplar_path):
    payload["exemplar"] = json.load(open(exemplar_path))

out = os.path.join(DATA, "results.js")
with open(out, "w") as f:
    f.write("window.RESULTS = " + json.dumps(payload) + ";\n")
print(f"{out}  {os.path.getsize(out) // 1024} KB  {len(names)} frames")
