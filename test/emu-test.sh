#!/usr/bin/env bash
# Run the p-code emulation test (test/emu/emu_cases.txt).   test/emu-test.sh [out.txt] [LANG_ID]
# With BASS=/path/to/bass, emu.bin/emu.lbl are rebuilt from the cases first.
set -euo pipefail
: "${GHIDRA_INSTALL_DIR:?set GHIDRA_INSTALL_DIR}"
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=$(readlink -m "${1:-${TMPDIR:-/tmp}/spc-emu.txt}"); LANG_ID=${2:-spc700:LE:16:default}
PROJ=$(mktemp -d "${TMPDIR:-/tmp}/spc-emu.XXXXXX")
trap 'rm -rf "$PROJ"' EXIT
[[ -n ${BASS:-} ]] && python3 "$HERE/emu/make_emu.py" "$BASS" >/dev/null
"$GHIDRA_INSTALL_DIR/support/analyzeHeadless" "$PROJ" p -import "$HERE/emu/emu.bin" \
	-loader BinaryLoader -processor "$LANG_ID" -noanalysis -scriptPath "$HERE" \
	-postScript SpcEmuTest.java "$HERE/emu/emu_cases.txt" "$HERE/emu/emu.lbl" "$OUT" \
	-deleteProject >"$PROJ/log.txt" 2>&1 || { tail -40 "$PROJ/log.txt" >&2; exit 1; }
cat "$OUT"
grep -q " 0 failed" "$OUT"
