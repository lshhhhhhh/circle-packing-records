#!/usr/bin/env python3
"""Standalone verifier for circle-packing claims (perimeter-4 rectangle, maximize sum of radii).

INDEPENDENT of the repository that produced the claims: this file imports only
mpmath (pip install mpmath). Give it to any agent or human for adversarial review.

Input format (same as github.com/DominikKamp/Packing rectangle entries):
    line 1: n                     (number of circles)
    line 2: claimed sum of radii  (decimal)
    lines 3..n+2: x y r           (one circle per line, whitespace-separated)

Checks performed at 60 significant digits, treating each coordinate as the exact
rational value of its decimal literal:
    C1  all radii strictly positive
    C2  no two circles overlap:  dist(i,j) - (r_i + r_j) >= 0   for all pairs
    C3  minimal axis-aligned bounding rectangle satisfies  width + height <= 2
    C4  sum of radii matches the claimed value               (agreement < 1e-12)

Exit code 0 iff C1-C4 all hold. Prints exact worst margins so a reviewer can
judge how much numerical room the construction has.

Usage:
    python verify.py coords_n24.txt [--record 2.535344050819014]

With --record, additionally reports whether the verified sum strictly exceeds
the given record value (does NOT affect the exit code: beating a record is a
claim about the state of the literature, not about this file's validity).
"""

import sys

from mpmath import mp, mpf, sqrt

mp.dps = 60


def fail(msg: str) -> None:
    print(f"FAIL  {msg}")
    sys.exit(1)


def main() -> None:
    argv = sys.argv[1:]
    record = None
    if "--record" in argv:
        idx = argv.index("--record")
        record = mpf(argv[idx + 1])
        del argv[idx : idx + 2]          # 连同取值一起从位置参数中移除
    if len(argv) != 1:
        print(__doc__)
        sys.exit(2)
    args = argv

    lines = [ln.strip() for ln in open(args[0], encoding="utf-8") if ln.strip()]
    n = int(lines[0])
    claimed_sum = mpf(lines[1])
    rows = [[mpf(tok) for tok in ln.split()] for ln in lines[2:]]
    if len(rows) != n or any(len(r) != 3 for r in rows):
        fail(f"expected {n} rows of 'x y r', got {len(rows)} rows")

    # C1: positive radii
    min_r = min(r[2] for r in rows)
    if min_r <= 0:
        fail(f"C1 nonpositive radius: {min_r}")
    print(f"PASS  C1 all radii > 0              (min radius = {mp.nstr(min_r, 12)})")

    # C2: pairwise non-overlap
    worst = mpf(10)
    worst_pair = (-1, -1)
    for i in range(n):
        xi, yi, ri = rows[i]
        for j in range(i + 1, n):
            xj, yj, rj = rows[j]
            slack = sqrt((xi - xj) ** 2 + (yi - yj) ** 2) - (ri + rj)
            if slack < worst:
                worst, worst_pair = slack, (i, j)
    if worst < 0:
        fail(f"C2 circles {worst_pair} overlap by {mp.nstr(-worst, 8)}")
    print(f"PASS  C2 no overlaps                (tightest pair {worst_pair}, slack = {mp.nstr(worst, 8)})")

    # C3: bounding rectangle perimeter
    width = max(r[0] + r[2] for r in rows) - min(r[0] - r[2] for r in rows)
    height = max(r[1] + r[2] for r in rows) - min(r[1] - r[2] for r in rows)
    slack = 2 - (width + height)
    if slack < 0:
        fail(f"C3 width+height exceeds 2 by {mp.nstr(-slack, 8)}")
    print(f"PASS  C3 width+height <= 2          (slack = {mp.nstr(slack, 8)})")

    # C4: claimed sum
    actual = sum(r[2] for r in rows)
    if abs(actual - claimed_sum) > mpf("1e-12"):
        fail(f"C4 claimed sum {claimed_sum} but coordinates give {mp.nstr(actual, 25)}")
    print(f"PASS  C4 sum of radii               = {mp.nstr(actual, 25)}")

    if record is not None:
        margin = actual - record
        verdict = "STRICTLY EXCEEDS" if margin > 0 else "does NOT exceed"
        print(f"INFO  vs record {mp.nstr(record, 20)}: {verdict} by {mp.nstr(margin, 8)}")

    print("\nALL CHECKS PASSED")


if __name__ == "__main__":
    main()
