#!/usr/bin/env python3
"""Build SPC700 test inputs.

  make_spc.py driver <sm_spc.asm> <out.bin> <out.spc>
      PVSnesLib's sm_spc.asm (the SNESMOD driver as WLA-DX .byte lines) -> raw driver binary
      and a .spc snapshot with the driver at $0400 and PC = $0400, its entry point (where
      PVSnesLib uploads and starts it). RAM elsewhere is zero.
  make_spc.py dump <ram.bin> <PC> <A> <X> <Y> <PSW> <SP> <out.spc>
      64 KB of SPC700 RAM and CPU registers saved from an emulator -> .spc snapshot, the way
      real-world .spc files are made (registers decimal, as MAME's Lua state prints them).
"""
import re
import struct
import sys


def spc(ram, pc, a=0, x=0, y=0, psw=0x02, sp=0xEF):
    hdr = bytearray(0x100)
    hdr[0:33] = b"SNES-SPC700 Sound File Data v0.30"
    hdr[33:35] = b"\x1a\x1a"
    hdr[35] = 27           # no ID666 tag
    hdr[36] = 30           # minor version
    hdr[37:39] = struct.pack("<H", pc)
    hdr[39:44] = bytes([a, x, y, psw, sp])
    assert len(ram) == 0x10000
    return bytes(hdr) + bytes(ram) + bytes(128) + bytes(64) + bytes(64)


if sys.argv[1] == "driver":
    src, out_bin, out_spc = sys.argv[2:5]
    data = bytearray()
    for line in open(src):
        m = re.match(r"\s*\.byte\s+(.*)", line)
        if m:
            data += bytes(int(v.strip().lstrip("$"), 16) for v in m.group(1).split(","))
    size = int(re.search(r"\.define SM_SPC_SIZE ([0-9A-Fa-f]+)h", open(src).read()).group(1), 16)
    assert len(data) == size, (len(data), size)
    open(out_bin, "wb").write(data)
    ram = bytearray(0x10000)
    ram[0x400:0x400 + len(data)] = data
    open(out_spc, "wb").write(spc(ram, 0x400))
elif sys.argv[1] == "dump":
    ram = open(sys.argv[2], "rb").read()
    pc, a, x, y, psw, sp = (int(v) for v in sys.argv[3:9])
    open(sys.argv[9], "wb").write(spc(ram, pc, a, x, y, psw, sp))
else:
    raise SystemExit(__doc__)
