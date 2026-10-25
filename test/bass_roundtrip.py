#!/usr/bin/env python3
"""Assembler round trip for the 65816-style variant: re-assemble Ghidra's spc700:LE:16:65816
text with bass (its spc700.arch table defines that syntax) and compare the bytes.

  bass_roundtrip.py <ghidra.txt> <bass> <workdir> [--label L]

Each record is assembled at its own address. bass picks the direct-page or absolute form from
the operand value, so a mismatch is retried once with the explicit .b/.w size suffix that the
table also defines; a record passes when either spelling reproduces Ghidra's bytes.
"""
import argparse
import os
import re
import subprocess

ap = argparse.ArgumentParser()
ap.add_argument("ghidra")
ap.add_argument("bass")
ap.add_argument("work")
ap.add_argument("--label", default="")
a = ap.parse_args()
os.makedirs(a.work, exist_ok=True)

recs = []
for line in open(a.ghidra):
    p = line.rstrip("\n").split(" ", 2)
    if len(p) == 3 and re.fullmatch(r"[0-9a-f]{4}", p[0]) and not p[2].startswith("BAD"):
        recs.append((int(p[0], 16), p[1], p[2]))


BRANCH = {"bpl", "bmi", "bvc", "bvs", "bcc", "bcs", "bne", "beq", "bra", "bbs", "bbc"}


def to_bass(t, suffix="", addr=0, size=0):
    mn, _, ops = t.partition(" ")
    if mn.lower() in BRANCH:
        # targets wrap at $FFFF; give bass the unwrapped value it range-checks
        m = re.search(r"0x([0-9a-f]+)$", ops)
        tgt = int(m.group(1), 16)
        nxt = addr + size
        if tgt - nxt < -128:
            tgt += 0x10000
        elif tgt - nxt > 127:
            tgt -= 0x10000
        ops = ops[:m.start()] + ("%d" % tgt if tgt >= 0 else "(%d)" % tgt)
    # decimal numbers: bass's lexer rejects some "$h:" forms (e.g. "set $0:0")
    ops = re.sub(r"0x([0-9a-f]+)", lambda m: "%d" % int(m.group(1), 16), ops.lower())
    return (mn.lower() + suffix + " " + ops).strip()


def assemble(lines):
    src = os.path.join(a.work, "rt.asm")
    out = os.path.join(a.work, "rt.bin")
    with open(src, "w") as f:
        f.write('arch spc700\noutput "rt.bin", create\nfill $40000\n')
        for i, (addr, text) in enumerate(lines):
            f.write("origin $%x\nbase $%x\n%s\n" % (4 * i, addr, text))
    r = subprocess.run([a.bass, src], capture_output=True, text=True)
    data = open(out, "rb").read() if os.path.exists(out) else b""
    return data, r.stderr


def run(texts):
    data, err = assemble([(addr, t) for (addr, _, _), t in zip(recs, texts)])
    if not data:
        raise SystemExit("bass failed: " + err[:2000])
    return [data[4 * i:4 * i + len(b) // 2].hex() for i, (_, b, _) in enumerate(recs)]


first = run([to_bass(t, "", addr, len(b) // 2) for addr, b, t in recs])
ok = [g == b for g, (_, b, _) in zip(first, recs)]
retry = [to_bass(t, (".w" if len(b) == 6 else ".b") if not k else "", addr, len(b) // 2)
         for k, (addr, b, t) in zip(ok, recs)]
second = run(retry)
bad = []
for i, (addr, b, t) in enumerate(recs):
    if ok[i] or second[i] == b:
        continue
    bad.append((addr, b, t, first[i], second[i]))
n = len(recs)
print(f"{a.label}: {n} records, bass reproduces {n - len(bad)} ({100 * (n - len(bad)) / max(n, 1):.2f}%)"
      f" ({sum(ok)} without a size suffix)")
for addr, b, t, f1, f2 in bad[:20]:
    print(f"  {addr:04x} {b} {t!r} -> {f1} / {f2}")
