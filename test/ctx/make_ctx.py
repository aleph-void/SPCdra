#!/usr/bin/env python3
"""PSW.P decode-context test program (test/ctx-test.sh), hand-assembled at $0200. Each entry:
(bytes, native-syntax text, the PSW.P decode context the instruction must have, i.e. the direct
page of its operand, $00xx or $01xx; Ghidra shows the operand byte either way)."""
import sys
PROG = [
    ("40", "SETP", 0),
    ("0d", "PUSH PSW", 1),         # saves P=1
    ("20", "CLRP", 1),
    ("e412", "MOV A,0x12", 0),     # $0012
    ("8e", "POP PSW", 0),          # restores P=1
    ("e434", "MOV A,0x34", 1),     # $0134
    ("20", "CLRP", 1),
    ("0d", "PUSH PSW", 0),         # saves P=0
    ("40", "SETP", 0),
    ("e456", "MOV A,0x56", 1),     # $0156
    ("8e", "POP PSW", 1),          # restores P=0
    ("e478", "MOV A,0x78", 0),     # $0078
    ("ff", "STOP", 0),
]
if __name__ == "__main__":
    open(sys.argv[1], "wb").write(bytes.fromhex("".join(b for b, _, _ in PROG)))
    with open(sys.argv[2], "w") as f:
        a = 0x200
        for b, t, p in PROG:
            f.write(f"{a:04x} P{p} {t}\n")
            a += len(b) // 2
