import argparse
import os
import subprocess

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("start")
    ap.add_argument("--seconds", type=int, default=12)
    ap.add_argument("--fps", type=int, default=2)
    ap.add_argument("--width", type=int, default=420)
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "frames"))
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    for old in os.listdir(args.out):
        os.remove(os.path.join(args.out, old))
    subprocess.run(
        ["ffmpeg", "-nostdin", "-loglevel", "error", "-ss", args.start,
         "-t", str(args.seconds), "-i", args.video,
         "-vf", f"fps={args.fps},scale={args.width}:-2", "-q:v", "4",
         "-y", os.path.join(args.out, "f%03d.jpg")],
        check=True,
    )
    print(f"{len(os.listdir(args.out))} frames -> {args.out}")

if __name__ == "__main__":
    main()
