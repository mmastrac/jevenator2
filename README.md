# Jevenator 2: Judgment Day

Region-scan object localisation on a diffusion LLM.

## Run

Cached results, no server:

```bash
open index.html
```

With the API, for live scans:

```bash
DJEV_URL=http://127.0.0.1:8011 python3 server/app.py --port 8020
```

Then put `http://localhost:8020` in the API field.

## Regenerate

```bash
python3 scripts/extract_frames.py VIDEO 00:44:17 --seconds 12 --fps 2
DJEV_URL=http://127.0.0.1:8011 python3 scripts/scan_frames.py --cols 7 --rows 5
DJEV_URL=http://127.0.0.1:8011 python3 scripts/scan_refs.py
DJEV_URL=http://127.0.0.1:8011 python3 scripts/scan_tracks.py --cols 7 --rows 5
python3 scripts/build_results.py
```

## Layout

| path | |
|---|---|
| `index.html` | viewer, reads `data/results.js` |
| `data/frames/` | extracted frames |
| `data/maps.json` | per-frame region probabilities |
| `data/temporal.json` | previous-frame and wrong-hint arms |
| `data/results.js` | built from the above, what the page loads |
| `data/refs/` | reference subjects |
| `data/scenes/` | scenes the references are matched against |
| `data/exemplar.json` | reference match results, both channels |
| `data/tracks.json` | each reference scanned across every frame |
| `server/regions.py` | thresholding and box geometry, no dependencies |
| `server/gridscan.py` | grid overlay and region queries |
| `server/app.py` | static files plus `POST /api/scan` |

## Modes

| mode | |
|---|---|
| `single` | one read per frame |
| `averaged` | region probabilities averaged over 5 frames before thresholding |
| `prev` | previous frame's regions supplied in the prompt |
| `wrong` | a fixed region group the subject is not in |
| `reference` | a reference photo instead of a description, one entry per target |

`wrong` is the control for `prev`. Requires Pillow for live scanning; the cached
viewer needs nothing.

## Reference matching

`scripts/scan_refs.py` matches a reference subject to a region, sending the
reference two ways: `attached` as its own image part, `composited` into a band
above the scene. Results are in `data/exemplar.json`; the page does not show
them. The `shapes` scene is the control that the reference is used at all. In
the `night` scene the expected regions are `CFI` for the boy and `DG` for the
man in sunglasses; `dyson` is a face that is not in that scene, so its expected
result is no region at all.
