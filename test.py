import re

NL_NUMS = {
    'eerste': 1, 'tweede': 2, 'derde': 3, 'vierde': 4, 'vijfde': 5,
    'zesde': 6, 'zevende': 7, 'achtste': 8, 'negende': 9, 'tiende': 10,
    'een': 1, 'twee': 2, 'drie': 3, 'vier': 4, 'vijf': 5,
    'zes': 6, 'zeven': 7, 'acht': 8, 'negen': 9, 'tien': 10,
}

def to_num(s):
    s = s.strip().lower()
    if s in NL_NUMS:
        return NL_NUMS[s]
    try:
        return float(s)
    except ValueError:
        return None

def parse_input(raw: str) -> str:
    s = raw.lower().replace(',', ' ')
    s = re.sub(r'\s+', ' ', s).strip()

    # Aantal robots
    n_match = re.search(r'(\d+)\s*robots?', s)
    if not n_match:
        raise ValueError("Aantal robots niet gevonden.")
    N = int(n_match.group(1))

    # Startbot
    start_match = re.search(r'start(?:bot|punt|positie)?\s*(\d+)', s)
    if not start_match:
        raise ValueError("Startbot niet gevonden.")
    startbot = int(start_match.group(1))
    if not (1 <= startbot <= N):
        raise ValueError(f"Startbot {startbot} buiten bereik (1–{N}).")

    work = s
    work = re.sub(r'start(?:bot|punt|positie)?\s*\d+', '', work)
    work = re.sub(r'\d+\s*robots?', '', work, count=1)

    robot_dists = [None] * N

    # Individuele robots: "eerste robot 7 meter"
    for m in re.finditer(r'(?:de\s+)?(\w+)\s+robot\s+(?:op\s+)?([\d.]+)\s*meter', work):
        idx = to_num(m.group(1))
        if idx is not None and 1 <= int(idx) <= N:
            robot_dists[int(idx) - 1] = float(m.group(2))

    # Groepen: "eerste/volgende/laatste X robots Y meter"
    cursor = 0
    for m in re.finditer(
        r'(?:eerste|volgende|laatste)?\s*(\d+)\s*robots?\s+(?:op\s+)?([\d.]+)\s*meter',
        work
    ):
        count = int(m.group(1))
        dist = float(m.group(2))
        for i in range(cursor, min(cursor + count, N)):
            if robot_dists[i] is None:
                robot_dists[i] = dist
        cursor += count

    # Overige / alle
    for m in re.finditer(r'overige\s+(?:robots?\s+)?(?:op\s+)?([\d.]+)\s*meter', work):
        dist = float(m.group(1))
        for i in range(N):
            if robot_dists[i] is None:
                robot_dists[i] = dist

    # Uniform: alleen een afstand zonder groepsspecificatie
    if all(d is None for d in robot_dists):
        m = re.search(r'(?:op\s+)?([\d.]+)\s*meters?', work)
        if m:
            dist = float(m.group(1))
            robot_dists = [dist] * N

    if any(d is None for d in robot_dists):
        missing = [i + 1 for i, d in enumerate(robot_dists) if d is None]
        raise ValueError(f"Afstand voor robot(s) {missing} niet gevonden.")

    # N robots → N-1 gaps (gap[i] = afstand van robot i naar robot i+1)
    gaps = [robot_dists[i + 1] for i in range(N - 1)]

    dist_str = ', '.join(
        str(int(g)) if g == int(g) else str(g) for g in gaps
    )
    return f"ROBOTS:{N} | DATA:{dist_str} | STARTBOT: {startbot}"


# --- CLI ---
if __name__ == "__main__":
    print("Robot Position Parser  (type 'quit' om te stoppen)\n")
    while True:
        try:
            inp = input("Input: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if inp.lower() in ('quit', 'exit', 'stop'):
            break
        if not inp:
            continue
        try:
            print(parse_input(inp))
        except ValueError as e:
            print(f"Fout: {e}")
        print()

    