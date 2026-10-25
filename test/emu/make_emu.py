#!/usr/bin/env python3
"""Build emu.asm and emu.lbl from emu_cases.txt (see that file), then assemble with bass.

  make_emu.py [bass]      -> emu.asm, emu.lbl, and emu.bin (if bass is given)
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
cases = [l for l in open(os.path.join(HERE, "emu_cases.txt"))
         if l.strip() and not l.startswith("#")]
asm = ["arch spc700", 'output "emu.bin", create']
labels = []
for i, line in enumerate(cases):
    name, _, code = [x.strip() for x in line.split("|")[:3]]
    addr = 0x400 + 0x40 * i
    asm += ["origin $%x" % addr, "base $%x" % addr, "%s:" % name]
    labels.append((name, addr))
    for st in code.split(" ; "):
        st = re.sub(r"@(\w+)", name + "_" + r"\1", st.strip())
        m = re.match(r"(%s_\w+):\s*(.*)" % name, st)
        if m:
            asm.append(m.group(1) + ":")
            st = m.group(2)
        if st:
            asm.append(st)
    asm.append("stp")
end = 0x400 + 0x40 * len(cases)
asm += ["origin $%x" % end, "base $%x" % end]
asm.append("jmpidx_t:")                        # target used by the jmpidx case
asm.append("lda #$00")
asm.append("stp")
open(os.path.join(HERE, "emu.asm"), "w").write("\n".join(asm) + "\n")
if len(sys.argv) > 1:
    subprocess.run([sys.argv[1], "emu.asm"], cwd=HERE, check=True)
with open(os.path.join(HERE, "emu.lbl"), "w") as f:
    for name, addr in labels:
        f.write("%s %04x\n" % (name, addr))
    f.write("jmpidx_t %04x\n" % end)
