import base64
import http.client
import io
import json
import os
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont

from regions import blob, box, labels, smooth

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXY"
DJEV_URL = os.environ.get("DJEV_URL", "http://127.0.0.1:8011")
BATCH = 9

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

def band(scene, ref, n, caption="REFERENCE"):
    scene = scene.convert("RGB")
    w, h = scene.size
    height = 120
    thumb = ref.convert("RGB").copy()
    thumb.thumbnail((height - 20, height - 20))
    out = Image.new("RGB", (w, h + height), (20, 20, 20))
    out.paste(thumb, (10, 10))
    d = ImageDraw.Draw(out)
    d.rectangle([9, 9, 10 + thumb.size[0], 10 + thumb.size[1]], outline=(255, 255, 0), width=2)
    d.text((thumb.size[0] + 26, 24), caption, fill=(255, 255, 0), font=_font(20))
    out.paste(overlay(scene, n), (0, height))
    return out

def scan(im, target, n=5, seed=7, hint=None, reference=None, channel="attached"):
    composited = reference is not None and channel == "composited"
    if composited:
        scene_img = band(im, reference, n)
    else:
        scene_img = overlay(im, n)
    buf = io.BytesIO()
    scene_img.save(buf, "PNG")
    url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    text = f"A photograph divided into {n * n} labelled regions."
    if composited:
        text = ("A reference subject in the band at the top, and below it a photograph "
                f"divided into {n * n} labelled regions.")
    if hint:
        text += f" In the previous frame the subject was found in regions {hint}."

    attached = reference is not None and channel == "attached"
    if attached:
        headline = "Report which labelled regions of the second image contain the subject of the first image."

        def question(c):
            return f"Does region {c} of the second image contain the subject shown in the first image?"
    elif composited:
        headline = "Report which labelled regions contain the subject shown in the reference band."

        def question(c):
            return f"Does the region labelled {c} contain the subject shown in the reference band?"
    else:
        headline = f"Report which labelled regions contain {target}."

        def question(c):
            return f"Does the region labelled {c} contain {target}?"

    parsed = urlparse(DJEV_URL)
    if attached:
        rbuf = io.BytesIO()
        reference.convert("RGB").save(rbuf, "PNG")
        rurl = "data:image/png;base64," + base64.b64encode(rbuf.getvalue()).decode()
        parts = [
            {"type": "text", "text": "First image, the reference subject:"},
            {"type": "image_url", "image_url": {"url": rurl}},
            {"type": "text", "text": "Second image, " + text[0].lower() + text[1:]},
            {"type": "image_url", "image_url": {"url": url}},
        ]
    else:
        parts = [
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": url}},
        ]

    conn = http.client.HTTPConnection(parsed.hostname, parsed.port or 80, timeout=300)
    probs = {}
    try:
        for i in range(0, n * n, BATCH):
            group = labels(n)[i : i + BATCH]
            schema = {
                "instructions": headline,
                "samples": 1,
                "questions": [
                    {
                        "id": c,
                        "type": "noul",
                        "instructions": question(c),
                    }
                    for c in group
                ],
            }
            body = json.dumps(
                {
                    "seed": seed,
                    "messages": [
                        {"role": "system", "content": json.dumps(schema)},
                        {"role": "user", "content": parts},
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
