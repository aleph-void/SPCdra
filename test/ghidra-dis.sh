#!/usr/bin/env bash
# Fixed-stride Ghidra disassembly of a raw SPC700 corpus.
#   test/ghidra-dis.sh <LANG_ID> <raw.bin> <out.txt> <stride> [dis|pcode]
set -euo pipefail
LANG_ID=$1; BIN=$(readlink -f "$2"); OUT=$(readlink -m "$3"); STRIDE=$4; MODE=${5:-dis}
: "${GHIDRA_INSTALL_DIR:?set GHIDRA_INSTALL_DIR}"
HERE=$(cd "$(dirname "$0")" && pwd)
PROJ=$(mktemp -d "${TMPDIR:-/tmp}/spc-dis.XXXXXX")
trap 'rm -rf "$PROJ"' EXIT
"$GHIDRA_INSTALL_DIR/support/analyzeHeadless" "$PROJ" p \
	-import "$BIN" -loader BinaryLoader -processor "$LANG_ID" \
	-noanalysis -scriptPath "$HERE" -postScript SpcDumpDisasm.java "$OUT" "$STRIDE" "$MODE" \
	-deleteProject >"$PROJ/log.txt" 2>&1 || { tail -40 "$PROJ/log.txt" >&2; exit 1; }
[[ -s $OUT ]] || { grep -E "ERROR|Exception" "$PROJ/log.txt" | head -40 >&2; exit 1; }
