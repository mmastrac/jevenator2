import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "server"))

from PIL import Image

import gridscan
import regions

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FRAMES = os.path.join(ROOT, "data", "frames")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="a boy with light blond hair")
    ap.add_argument("--cols", type=int, default=5)
    ap.add_argument("--rows", type=int, default=5)
    ap.add_argument("--threshold", type=float, default=0.55)
    ap.add_argument("--wrong-hint", default="",
                    help="control: a region group the subject is not in")
    args = ap.parse_args()

    names = sorted(os.listdir(FRAMES))
    maps, times = {}, []
    for name in names:
        t = time.perf_counter()
        im = Image.open(os.path.join(FRAMES, name))
        maps[name] = gridscan.scan(im, args.target, cols=args.cols, rows=args.rows)
        times.append((time.perf_counter() - t) * 1e3)
        print(f"  {name}  {times[-1]:6.0f} ms", flush=True)
    json.dump({"maps": maps, "times": times, "cols": args.cols, "rows": args.rows},
              open(os.path.join(ROOT, "data", "maps.json"), "w"))

    arms = {}
    for arm in ("B_true", "C_wrong"):
        out, prev = {}, None
        for name in names:
            hint = args.wrong_hint if arm == "C_wrong" else prev
            im = Image.open(os.path.join(FRAMES, name))
            out[name] = gridscan.scan(im, args.target, cols=args.cols, rows=args.rows, hint=hint)
            cells = regions.blob(out[name], args.cols, args.rows, args.threshold)
            prev = ", ".join(regions.labels(args.cols, args.rows)[c] for c in cells) or None
        arms[arm] = out
        print(f"  {arm} done", flush=True)
    json.dump(arms, open(os.path.join(ROOT, "data", "temporal.json"), "w"))
    print(f"mean {sum(times)/len(times):.0f} ms/frame over {len(times)} frames")

if __name__ == "__main__":
    main()
