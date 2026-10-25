#!/usr/bin/env bash
# SPC loader test: a synthetic .spc (code at $0400, saved PC $0400, DSP registers KON=$5A and
# V3SRCN=$07) imported without naming the loader: the RAM, the DSP overlay with register names
# and the entry point must be there.     test/loader-test.sh [workdir]
set -euo pipefail
: "${GHIDRA_INSTALL_DIR:?set GHIDRA_INSTALL_DIR}"
HERE=$(cd "$(dirname "$0")" && pwd)
WORK=$(mkdir -p "${1:-${TMPDIR:-/tmp}/spc-loader}" && cd "${1:-${TMPDIR:-/tmp}/spc-loader}" && pwd)
python3 - "$WORK/t.spc" <<'PY'
import struct, sys
hdr = bytearray(0x100)
hdr[0:33] = b"SNES-SPC700 Sound File Data v0.30"
hdr[33:37] = bytes([0x1a, 0x1a, 27, 30])
hdr[37:44] = struct.pack("<H", 0x400) + bytes([0, 0, 0, 0x02, 0xef])   # PC, A X Y PSW SP
ram = bytearray(0x10000)
ram[0x400:0x404] = bytes.fromhex("e8422ffe")                          # mov a,#$42 ; bra self
dsp = bytearray(128)
dsp[0x4c], dsp[0x34] = 0x5a, 0x07                                     # KON, V3SRCN
open(sys.argv[1], "wb").write(bytes(hdr) + bytes(ram) + bytes(dsp) + bytes(128))
PY
PROJ=$(mktemp -d "${TMPDIR:-/tmp}/spc-ldr.XXXXXX")
trap 'rm -rf "$PROJ"' EXIT
"$GHIDRA_INSTALL_DIR/support/analyzeHeadless" "$PROJ" p -import "$WORK/t.spc" \
	-scriptPath "$HERE" -postScript SpcLoaderCheck.java "$WORK/loader.txt" \
	-deleteProject >"$PROJ/log.txt" 2>&1 || { tail -40 "$PROJ/log.txt" >&2; exit 1; }
python3 - "$WORK/loader.txt" <<'PY'
import sys
got = open(sys.argv[1]).read()
want = ["dspblock DSP::0000 128 overlay=true", "kon 5a KON", "v3srcn 07 V3SRCN",
        "entry 0400 MOV A,#0x42"]
ok = [w for w in want if w in got]
for w in want:
    if w not in got:
        print("FAIL missing", repr(w))
print(f"loader: {len(ok)} passed, {len(want) - len(ok)} failed")
if len(ok) != len(want):
    print(got)
sys.exit(0 if len(ok) == len(want) else 1)
PY
