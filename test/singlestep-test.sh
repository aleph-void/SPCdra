#!/usr/bin/env bash
# p-code check against SingleStepTests/spc700 (fetched by test/fetch-singlestep.py, never committed).
#   test/singlestep-test.sh <tests.json> <out.txt> [LANG_ID]
set -euo pipefail
: "${GHIDRA_INSTALL_DIR:?set GHIDRA_INSTALL_DIR}"
HERE=$(cd "$(dirname "$0")" && pwd)
TESTS=$(readlink -f "$1"); OUT=$(readlink -m "$2"); LANG_ID=${3:-spc700:LE:16:default}
PROJ=$(mktemp -d "${TMPDIR:-/tmp}/spc-sst.XXXXXX")
trap 'rm -rf "$PROJ"' EXIT
head -c 256 /dev/zero > "$PROJ/zero.bin"
"$GHIDRA_INSTALL_DIR/support/analyzeHeadless" "$PROJ" p -import "$PROJ/zero.bin" \
	-loader BinaryLoader -processor "$LANG_ID" -noanalysis \
	-scriptPath "$HERE" -postScript SpcSingleStep.java "$TESTS" "$OUT" \
	-deleteProject >"$PROJ/log.txt" 2>&1 || { tail -40 "$PROJ/log.txt" >&2; exit 1; }
tail -1 "$OUT"
