import argparse
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "server"))

from PIL import Image

import gridscan
import regions

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "data")

DESCRIPTIONS = {
    "shape_triangle": "Red triangle. Control: a subject the model cannot mistake.",
    "shape_circle": "Blue circle. Control: the other shape in the same scene.",
    "john_daylight": "John Connor, lit reference.",
    "john_photo": "John Connor, reference.",
    "terminator": "The Terminator.",
    "dyson": "Miles Dyson.",
}

SCENES = {
    "shapes": {
        "n": 3,
        "truth": {"shape_triangle": "B", "shape_circle": "F"},
        "refs": ["shape_triangle", "shape_circle"],
    },
    "night": {
        "n": 3,
        "truth": {"john_daylight": "CFI", "john_photo": "CFI",
                  "terminator": "DG", "dyson": ""},
        "refs": ["john_daylight", "john_photo", "terminator", "dyson"],
    },
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="1,2,3")
    ap.add_argument("--threshold", type=float, default=0.5)
    args = ap.parse_args()
    seeds = [int(s) for s in args.seeds.split(",")]

    out = {"threshold": args.threshold, "seeds": seeds, "scenes": {}}
    for scene, cfg in SCENES.items():
        n = cfg["n"]
        img = Image.open(os.path.join(DATA, "scenes", f"{scene}.jpg"))
        out["scenes"][scene] = {"n": n, "labels": regions.labels(n),
                                "truth": cfg["truth"],
                                "descriptions": {k: DESCRIPTIONS[k] for k in cfg["refs"]},
                                "channels": {}}
        for channel in ("attached", "composited"):
            per_ref = {}
            for name in cfg["refs"]:
                ref = Image.open(os.path.join(DATA, "refs", f"{name}.jpg"))
                draws = [gridscan.scan(img, "", n=n, seed=s, reference=ref, channel=channel)
                         for s in seeds]
                mean = {lab: round(statistics.mean(d[lab] for d in draws), 4)
                        for lab in regions.labels(n)}
                found = regions.groups(mean, n, args.threshold)
                cells = found[0] if found else []
                got = "".join(regions.labels(n)[c] for c in cells)
                want = cfg["truth"][name]
                if not want:
                    outcome = "rejected" if not got else "false positive"
                elif got and set(got) & set(want):
                    outcome = "match"
                else:
                    outcome = "miss"
                per_ref[name] = {"probs": mean, "cells": got, "truth": want,
                                 "groups": ["".join(regions.labels(n)[c] for c in g) for g in found],
                                 "outcome": outcome, "hit": outcome in ("match", "rejected")}
                print(f"  {scene:7s} {channel:11s} {name:16s} -> {got or 'none':6s} "
                      f"(want {want or 'none'})", flush=True)
            out["scenes"][scene]["channels"][channel] = per_ref

    path = os.path.join(DATA, "exemplar.json")
    json.dump(out, open(path, "w"), indent=1)
    print(f"\nwrote {path}")

if __name__ == "__main__":
    main()
