ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXY"

def labels(n):
    return ALPHABET[: n * n]

def neighbours(i, n):
    r, c = divmod(i, n)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            rr, cc = r + dr, c + dc
            if (dr or dc) and 0 <= rr < n and 0 <= cc < n:
                yield rr * n + cc

def connected(cells, n):
    cells = set(cells)
    if len(cells) < 2:
        return True
    start = next(iter(cells))
    seen, stack = {start}, [start]
    while stack:
        for nb in neighbours(stack.pop(), n):
            if nb in cells and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return seen == cells

def blob(probs, n, threshold):
    labs = labels(n)
    on = {i for i, lab in enumerate(labs) if probs[lab] >= threshold}
    if not on:
        return []
    rows = [i // n for i in on]
    cols = [i % n for i in on]
    inside = [
        r * n + c
        for r in range(min(rows), max(rows) + 1)
        for c in range(min(cols), max(cols) + 1)
    ]
    keep = set(on)
    for cell in sorted(set(inside) - on, key=lambda i: -probs[labs[i]]):
        if connected(keep, n):
            break
        keep.add(cell)
    return sorted(keep)

def groups(probs, n, threshold):
    labs = labels(n)
    on = {i for i, lab in enumerate(labs) if probs[lab] >= threshold}
    if not on:
        return []
    out = []
    remaining = set(on)
    while remaining:
        start = max(remaining, key=lambda i: probs[labs[i]])
        seen, stack = {start}, [start]
        while stack:
            for nb in neighbours(stack.pop(), n):
                if nb in remaining and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        rows = [i // n for i in seen]
        cols = [i % n for i in seen]
        inside = {
            r * n + c
            for r in range(min(rows), max(rows) + 1)
            for c in range(min(cols), max(cols) + 1)
        }
        keep = set(seen)
        for cell in sorted(inside - on, key=lambda i: -probs[labs[i]]):
            if connected(keep, n):
                break
            keep.add(cell)
        out.append(sorted(keep))
        remaining -= seen
    return out

def box(cells, n):
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
    lo, hi = max(0, i - half), min(len(maps) - 1, i + half)
    window = maps[lo : hi + 1]
    return {lab: sum(m[lab] for m in window) / len(window) for lab in labels(n)}
