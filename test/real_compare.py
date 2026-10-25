#!/usr/bin/env python3
"""Compare Ghidra's analysed SPC700 listing with MAME.

  real_compare.py <ghidra.lst> <mamespc700dis> [--trace mame-trace.log ...] [--label L]

decode : every instruction Ghidra disassembled, re-decoded by MAME's spc700 disassembler.
trace  : every distinct PC of MAME execution traces of the SPC700 (debugger "trace" on
         :soundcpu), excluding the boot ROM page $FFC0-$FFFF, looked up in Ghidra's listing.
"""
import argparse
import bisect
import collections
import os
import re
import subprocess
import tempfile

from spcnorm import norm_ghidra, norm_mame, semantic, mame_not1_bug

ap = argparse.ArgumentParser()
ap.add_argument("lst")
ap.add_argument("dis")
ap.add_argument("--trace", action="append", default=[])
ap.add_argument("--label", default="")
ap.add_argument("--show", type=int, default=3)
a = ap.parse_args()

G = {}
for line in open(a.lst):
    p = line.rstrip("\n").split(" ", 3)
    if len(p) == 4:
        G[int(p[0], 16)] = (p[2], p[3])

with tempfile.TemporaryDirectory() as td:
    lf = os.path.join(td, "l.txt")
    with open(lf, "w") as f:
        for addr, (b, t) in sorted(G.items()):
            f.write("%x %s\n" % (addr, b))
    out = subprocess.run([a.dis, "-list", lf], capture_output=True, text=True).stdout
M = {}
for line in out.splitlines():
    p = line.split(" ", 2)
    M[int(p[0], 16)] = (p[1], p[2] if len(p) > 2 else "")


def agrees(b, t, mb, mt):
    op = int(b[:2], 16)
    if mb != b:
        return mame_not1_bug(b, t)
    gn, mn = norm_ghidra(t), norm_mame(mt)
    return gn == mn or semantic(gn, mn, op)


agree = 0
diff = collections.defaultdict(list)
for addr, (b, t) in sorted(G.items()):
    mb, mt = M[addr]
    if agrees(b, t, mb, mt):
        agree += 1
    else:
        diff[b[:2]].append((addr, b, t, mt))
print(f"{a.label} decode: {len(G)} Ghidra instructions, MAME agrees on {agree} "
      f"({100 * agree / max(len(G), 1):.2f}%)")
for op, v in sorted(diff.items(), key=lambda kv: -len(kv[1])):
    print(f"  [op={op}] {len(v)}")
    for addr, b, t, mt in v[: a.show]:
        print(f"      {addr:04x} {b} ghidra={t!r} mame={mt!r}")

if a.trace:
    T = {}
    for tf in a.trace:
        for line in open(tf, errors="replace"):
            m = re.match(r"([0-9A-F]{4}): (.*)$", line.strip())
            if m and int(m.group(1), 16) < 0xffc0:
                T[int(m.group(1), 16)] = m.group(2)
    starts = sorted(G)
    same = 0
    cls = collections.Counter()
    ex = collections.defaultdict(list)
    for pc, mt in sorted(T.items()):
        if pc in G:
            b, t = G[pc]
            gn, mn = norm_ghidra(t), norm_mame(mt)
            if gn == mn or semantic(gn, mn, int(b[:2], 16)) or mame_not1_bug(b, t):
                same += 1
                continue
            k = "decoded differently"
        else:
            i = bisect.bisect_right(starts, pc) - 1
            if i >= 0 and starts[i] < pc < starts[i] + len(G[starts[i]][0]) // 2:
                k = "inside another Ghidra instruction"
            else:
                k = "not disassembled"
        cls[k] += 1
        ex[k].append((pc, mt, G.get(pc)))
    cov = len(T) - cls["not disassembled"] - cls["inside another Ghidra instruction"]
    print(f"{a.label} trace: {len(T)} executed PCs; Ghidra disassembled {cov} "
          f"({100 * cov / max(len(T), 1):.2f}%), decoded {same} of those identically "
          f"({100 * same / max(cov, 1):.2f}%)")
    for k, c in cls.most_common():
        print(f"  {k}: {c}")
        for pc, mt, g in ex[k][: a.show]:
            print(f"      {pc:04x} mame={mt!r} ghidra={g[1] if g else None!r}")
