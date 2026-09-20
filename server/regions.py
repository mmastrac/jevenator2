ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

def labels(cols, rows=None):
    rows = cols if rows is None else rows
    total = cols * rows
    if total > len(ALPHABET):
        raise ValueError(f"{total} regions needs more than {len(ALPHABET)} labels")
    return ALPHABET[:total]

def neighbours(i, cols, rows):
    r, c = divmod(i, cols)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            rr, cc = r + dr, c + dc
            if (dr or dc) and 0 <= rr < rows and 0 <= cc < cols:
                yield rr * cols + cc

def connected(cells, cols, rows):
    cells = set(cells)
    if len(cells) < 2:
        return True
    start = next(iter(cells))
    seen, stack = {start}, [start]
    while stack:
        for nb in neighbours(stack.pop(), cols, rows):
            if nb in cells and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return seen == cells

def groups(probs, cols, rows, threshold):
    labs = labels(cols, rows)
    on = {i for i, lab in enumerate(labs) if probs[lab] >= threshold}
    if not on:
        return []
    out = []
    remaining = set(on)
    while remaining:
        start = max(remaining, key=lambda i: probs[labs[i]])
        seen, stack = {start}, [start]
        while stack:
            for nb in neighbours(stack.pop(), cols, rows):
                if nb in remaining and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        rs = [i // cols for i in seen]
        cs = [i % cols for i in seen]
        inside = {
            r * cols + c
            for r in range(min(rs), max(rs) + 1)
            for c in range(min(cs), max(cs) + 1)
        }
        keep = set(seen)
        for cell in sorted(inside - on, key=lambda i: -probs[labs[i]]):
            if connected(keep, cols, rows):
                break
            keep.add(cell)
        out.append(sorted(keep))
        remaining -= seen
    return out

def blob(probs, cols, rows, threshold):
    found = groups(probs, cols, rows, threshold)
    return found[0] if found else []

def box(cells, cols, rows):
    if not cells:
        return None
    rs = [c // cols for c in cells]
    cs = [c % cols for c in cells]
    return {
        "x": min(cs) / cols,
        "y": min(rs) / rows,
        "w": (max(cs) + 1 - min(cs)) / cols,
        "h": (max(rs) + 1 - min(rs)) / rows,
    }

def smooth(maps, i, half, cols, rows):
    lo, hi = max(0, i - half), min(len(maps) - 1, i + half)
    window = maps[lo : hi + 1]
    return {lab: sum(m[lab] for m in window) / len(window) for lab in labels(cols, rows)}
