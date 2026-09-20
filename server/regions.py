"""Region geometry and thresholding. No dependencies, mirrored by the page."""

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXY"


def labels(n):
    return ALPHABET[: n * n]


def blob(probs, n, threshold):
    """Regions above the threshold that touch the strongest one."""
    labs = labels(n)
    on = {i for i, lab in enumerate(labs) if probs[lab] >= threshold}
    if not on:
        return []
    start = max(on, key=lambda i: probs[labs[i]])
    seen, stack = {start}, [start]
    while stack:
        cur = stack.pop()
        r, c = divmod(cur, n)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                nb = rr * n + cc
                if 0 <= rr < n and 0 <= cc < n and nb in on and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
    return sorted(seen)


def box(cells, n):
    """Bounding box of a region group, as fractions of the image."""
    if not cells:
        return None
    rows = [c // n for c in cells]
    cols = [c % n for c in cells]
    return {
        "x": min(cols) / n,
        "y": min(rows) / n,
        "w": (max(cols) + 1 - min(cols)) / n,
        "h": (max(rows) + 1 - min(rows)) / n,
    }


def smooth(maps, i, half, n):
    """Average each region over a centred window of frames."""
    lo, hi = max(0, i - half), min(len(maps) - 1, i + half)
    window = maps[lo : hi + 1]
    return {lab: sum(m[lab] for m in window) / len(window) for lab in labels(n)}
