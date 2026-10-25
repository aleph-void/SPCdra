#!/usr/bin/env python3
"""Compare Ghidra SPC700 decodes (native syntax) with MAME's spc700 disassembler.

  compare.py <ghidra.txt> <mame.txt> [--label L] [--show N]

Both files: "<addr-hex> <bytes-hex> <text>" per record. exact = same length and identical
normalised text; semantic = also counting spelling-only differences. Differences are bucketed
by opcode.
"""
import argparse
import collections
import re

from spcnorm import norm_ghidra, norm_mame, semantic, mame_not1_bug

ap = argparse.ArgumentParser()
ap.add_argument("ghidra")
ap.add_argument("mame")
ap.add_argument("--label", default="")
ap.add_argument("--show", type=int, default=3)
a = ap.parse_args()


def load(path):
    recs = {}
    for line in open(path):
        p = line.rstrip("\n").split(" ", 2)
        if len(p) >= 2 and re.fullmatch(r"[0-9a-f]{4}", p[0]):
            recs[int(p[0], 16)] = (p[1], p[2] if len(p) > 2 else "")
    return recs


G, M = load(a.ghidra), load(a.mame)
n = exact = sem = 0
buckets = collections.defaultdict(list)
for addr in sorted(M):
    if addr not in G:
        continue
    n += 1
    gb, gt = G[addr]
    mb, mt = M[addr]
    op = int(mb[:2], 16)
    if gt.startswith("BAD"):
        buckets[("ghidra-undecoded", "%02x" % op)].append((addr, mb, gt, mt))
        continue
    if gb != mb:
        if mame_not1_bug(gb, gt):
            sem += 1
            buckets[("MAME NOT1 length bug (Ghidra checked against the encoding)", "%02x" % op)].append((addr, mb, gb + " " + gt, mt))
            continue
        buckets[("length", "%02x" % op)].append((addr, mb, gb + " " + gt, mt))
        continue
    gn, mn = norm_ghidra(gt), norm_mame(mt)
    if gn == mn:
        exact += 1
        sem += 1
    elif semantic(gn, mn, op):
        sem += 1
        buckets[("alias", "%02x" % op)].append((addr, mb, gt, mt))
    else:
        buckets[("text", "%02x" % op)].append((addr, mb, gt, mt))
print(f"{a.label}: {n} records, exact {exact} ({100*exact/max(n,1):.2f}%), "
      f"semantic {sem} ({100*sem/max(n,1):.2f}%)")
bycls = collections.Counter()
for (cls, op), v in buckets.items():
    bycls[cls] += len(v)
for cls, c in bycls.most_common():
    print(f"  {cls}: {c}")
for (cls, op), v in sorted(buckets.items(), key=lambda kv: (kv[0][0] != "text" and kv[0][0] != "length", -len(kv[1]))):
    print(f"  [{cls} op={op}] {len(v)}")
    for addr, b, gt, mt in v[: a.show if cls in ("text", "length") else 1]:
        print(f"      {addr:04x} {b:8s} ghidra={gt!r} mame={mt!r}")
