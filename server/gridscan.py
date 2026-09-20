"""Grid region scan against a DiffusionGemma structured-decision server."""

import base64
import http.client
import io
import json
import os
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont

from regions import blob, box, labels, smooth  # noqa: F401

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXY"
DJEV_URL = os.environ.get("DJEV_URL", "http://127.0.0.1:8011")
BATCH = 9  # past ten questions the server picks a format whose noul labels are multi-token


def _font(size):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def overlay(im, n):
    """Draw the labelled grid the model is asked about."""
    out = im.convert("RGB").copy()
    d = ImageDraw.Draw(out)
    w, h = out.size
    cw, ch = w / n, h / n
    font = _font(15)
    for i in range(1, n):
        d.line([(i * cw, 0), (i * cw, h)], fill=(255, 255, 0), width=2)
        d.line([(0, i * ch), (w, i * ch)], fill=(255, 255, 0), width=2)
    for idx, lab in enumerate(labels(n)):
        r, c = divmod(idx, n)
        x, y = c * cw + 3, r * ch + 2
        d.rectangle([x, y, x + 20, y + 20], fill=(0, 0, 0))
        d.text((x + 4, y + 2), lab, fill=(255, 255, 0), font=font)
    return out


def scan(im, target, n=5, seed=7, hint=None):
    """Per-region yes/no for one image. Returns label -> probability."""
    buf = io.BytesIO()
    overlay(im, n).save(buf, "PNG")
    url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    text = f"A photograph divided into {n * n} labelled regions."
    if hint:
        text += f" In the previous frame the subject was found in regions {hint}."

    parsed = urlparse(DJEV_URL)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port or 80, timeout=300)
    probs = {}
    try:
        for i in range(0, n * n, BATCH):
            group = labels(n)[i : i + BATCH]
            schema = {
                "instructions": f"Report which labelled regions contain {target}.",
                "samples": 1,
                "questions": [
                    {
                        "id": c,
                        "type": "noul",
                        "instructions": f"Does the region labelled {c} contain {target}?",
                    }
                    for c in group
                ],
            }
            body = json.dumps(
                {
                    "seed": seed,
                    "messages": [
                        {"role": "system", "content": json.dumps(schema)},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": text},
                                {"type": "image_url", "image_url": {"url": url}},
                            ],
                        },
                    ],
                }
            ).encode()
            conn.request(
                "POST", "/v1/chat/completions", body=body,
                headers={"content-type": "application/json"},
            )
            resp = conn.getresponse()
            raw = resp.read()
            if resp.status != 200:
                raise RuntimeError(f"{DJEV_URL} returned {resp.status}: {raw[:200]!r}")
            answers = json.loads(json.loads(raw)["choices"][0]["message"]["content"])["answers"]
            probs.update({c: answers[c]["noul"] for c in group})
    finally:
        conn.close()
    return probs
