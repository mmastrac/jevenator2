# Jevenator 2: Judgement Day

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
DJEV_URL=http://127.0.0.1:8011 python3 scripts/scan_frames.py
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

`wrong` is the control for `prev`. Requires Pillow for live scanning; the cached
viewer needs nothing.
