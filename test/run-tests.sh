#!/usr/bin/env bash
# SPC700 module test harness.
#
#   GHIDRA_INSTALL_DIR=/path/to/ghidra_12.1.4 [BASS=/path/to/bass] [SINGLESTEP=1] \
#   [REAL_SAMPLES=<dir>] test/run-tests.sh [workdir] [ncorpora]
#
# 1. regenerates and compiles both SLEIGH specs (tools/gen_spc700.py) and the SPC loader
# 2. builds a driver for MAME's spc700 disassembler (test/build-mame-dis.sh)
# 3. decode corpora (64 KB each: every opcode x 16 operand patterns + 12,288 random words,
#    seeds 1..ncorpora): native variant vs MAME (test/compare.py); with BASS, the 65816-style
#    variant re-assembled by bass with the variant's own table (test/bass_roundtrip.py)
# 4. every opcode decodes in both variants; p-code emulation cases (test/emu-test.sh) on both
# 5. SINGLESTEP=1: SingleStepTests/spc700, all 256,000 tests, both variants
# 6. REAL_SAMPLES=<dir>: SNESMOD driver and MAME-dumped .spc files (test/real-binaries.sh)
# Report: <workdir>/report.txt
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
MOD=$(dirname "$HERE")
WORK=$(mkdir -p "${1:-${TMPDIR:-/tmp}/spc-test}" && cd "${1:-${TMPDIR:-/tmp}/spc-test}" && pwd)
NCORP=${2:-3}
: "${GHIDRA_INSTALL_DIR:?set GHIDRA_INSTALL_DIR (Ghidra 12.1.4)}"
: > "$WORK/report.txt"
LANGS=(spc700:LE:16:default spc700:LE:16:65816)

echo "[1] SLEIGH + loader"
python3 "$MOD/tools/gen_spc700.py" "$MOD/data/languages" >/dev/null
for s in "$MOD"/data/languages/*.slaspec; do
	"$GHIDRA_INSTALL_DIR/support/sleigh" "$s" 2>&1 | grep -E "^ERROR" && exit 1 || true
done
[[ -e $GHIDRA_INSTALL_DIR/Ghidra/Processors/SPC700 ]] || ln -sfn "$MOD" "$GHIDRA_INSTALL_DIR/Ghidra/Processors/SPC700"
"$HERE/build-jar.sh"

echo "[2] MAME spc700 disassembler"
"$HERE/build-mame-dis.sh" "$WORK/bin" >/dev/null
DIS=$WORK/bin/mamespc700dis

echo "[3] decode corpora"
for seed in $(seq 1 "$NCORP"); do
	python3 "$HERE/gen_corpus.py" "$WORK/corpus$seed.bin" 12288 "$seed" >/dev/null
	"$HERE/ghidra-dis.sh" spc700:LE:16:default "$WORK/corpus$seed.bin" "$WORK/native$seed.txt" 4 &
	"$HERE/ghidra-dis.sh" spc700:LE:16:65816 "$WORK/corpus$seed.bin" "$WORK/s65816_$seed.txt" 4 &
	"$DIS" "$WORK/corpus$seed.bin" -stride 4 > "$WORK/mame$seed.txt"
	wait
	python3 "$HERE/compare.py" "$WORK/native$seed.txt" "$WORK/mame$seed.txt" --label "native seed $seed" \
		| tee -a "$WORK/report.txt"
	if [[ -n ${BASS:-} ]]; then
		python3 "$HERE/bass_roundtrip.py" "$WORK/s65816_$seed.txt" "$BASS" "$WORK/bass$seed" \
			--label "65816-style seed $seed, bass" | tee -a "$WORK/report.txt"
	fi
done
python3 - "$WORK" <<'PY' | tee -a "$WORK/report.txt"
import sys
for v in ("native", "s65816_"):
    seen = set()
    for l in open(f"{sys.argv[1]}/{v}1.txt"):
        p = l.split(" ", 2)
        if len(p) == 3 and not p[2].startswith("BAD"):
            seen.add(p[1][:2])
    print(f"every-opcode decode ({v.strip('_')}): {len(seen)}/256")
PY

echo "[4] emulation"
for l in "${LANGS[@]}"; do
	echo "$l $("$HERE/emu-test.sh" "$WORK/emu-$l.txt" "$l" | tail -1)" | tee -a "$WORK/report.txt"
done

if [[ -n ${SINGLESTEP:-} ]]; then
	echo "[5] SingleStepTests"
	[[ -s $WORK/singlestep.json ]] || python3 -I "$HERE/fetch-singlestep.py" "$WORK/singlestep.json" 1000
	for l in "${LANGS[@]}"; do
		echo "$l $("$HERE/singlestep-test.sh" "$WORK/singlestep.json" "$WORK/singlestep-$l.txt" "$l")" \
			| tee -a "$WORK/report.txt"
	done
fi
if [[ -n ${REAL_SAMPLES:-} ]]; then
	echo "[6] real binaries"
	"$HERE/real-binaries.sh" "$REAL_SAMPLES" "$WORK/real" "$DIS" 10 | tee -a "$WORK/report.txt"
fi
echo "report: $WORK/report.txt"
