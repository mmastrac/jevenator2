import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "server"))

from PIL import Image  # noqa: E402

import gridscan  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FRAMES = os.path.join(ROOT, "data", "frames")
REFS = os.path.join(ROOT, "data", "refs")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cols", type=int, default=7)
    ap.add_argument("--rows", type=int, default=5)
    ap.add_argument("--channel", default="attached")
    ap.add_argument("--refs", default="john_daylight,john_photo,terminator,dyson")
    args = ap.parse_args()

    names = sorted(os.listdir(FRAMES))
    out = {"cols": args.cols, "rows": args.rows, "channel": args.channel, "tracks": {}}
    for ref_name in args.refs.split(","):
        ref = Image.open(os.path.join(REFS, f"{ref_name}.jpg"))
        maps, times = [], []
        for name in names:
            t = time.perf_counter()
            im = Image.open(os.path.join(FRAMES, name))
            maps.append(gridscan.scan(im, "", cols=args.cols, rows=args.rows,
                                      reference=ref, channel=args.channel))
            times.append((time.perf_counter() - t) * 1e3)
        out["tracks"][ref_name] = {"maps": maps, "ms": sum(times) / len(times)}
        print(f"  {ref_name:16s} {sum(times)/len(times):6.0f} ms/frame", flush=True)
    json.dump(out, open(os.path.join(ROOT, "data", "tracks.json"), "w"))
    print("wrote data/tracks.json")


if __name__ == "__main__":
    main()
