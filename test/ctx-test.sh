#!/usr/bin/env bash
# PSW.P decode-context test: SETP/CLRP and PUSH PSW ... POP PSW must give direct-page operands the
# right page (test/ctx/make_ctx.py).   test/ctx-test.sh <language-id> [workdir]
set -euo pipefail
: "${GHIDRA_INSTALL_DIR:?set GHIDRA_INSTALL_DIR}"
HERE=$(cd "$(dirname "$0")" && pwd)
LANG_ID=$1
WORK=$(mkdir -p "${2:-${TMPDIR:-/tmp}/spc-ctx}" && cd "${2:-${TMPDIR:-/tmp}/spc-ctx}" && pwd)
python3 "$HERE/ctx/make_ctx.py" "$WORK/ctx.bin" "$WORK/expect.txt"
PROJ=$(mktemp -d "${TMPDIR:-/tmp}/spc-ctx.XXXXXX")
trap 'rm -rf "$PROJ"' EXIT
"$GHIDRA_INSTALL_DIR/support/analyzeHeadless" "$PROJ" p -import "$WORK/ctx.bin" \
	-loader BinaryLoader -loader-baseAddr 0x200 -processor "$LANG_ID" -noanalysis \
	-scriptPath "$HERE" -postScript SpcListing.java "$WORK/ctx.txt" 200 0 \
	-deleteProject >"$PROJ/log.txt" 2>&1 || { tail -40 "$PROJ/log.txt" >&2; exit 1; }
python3 - "$WORK/expect.txt" "$WORK/ctx.txt" "$LANG_ID" <<'PY'
import sys
exp = [l.split(" ", 2) for l in open(sys.argv[1]).read().splitlines()]
got = {l.split(" ", 2)[0]: l.split(" ", 2)[1:] for l in open(sys.argv[2]).read().splitlines()}
native = sys.argv[3].endswith(":default")
ok = bad = 0
for a, p, t in exp:
    g = got.get(a)
    # the 65816-style variant spells the mnemonics differently: check the context there
    if g and g[0] == p and (not native or g[1] == t):
        ok += 1
    else:
        bad += 1
        print(f"FAIL {a}: expected {p} {t!r}, got {g!r}")
print(f"context: {ok} passed, {bad} failed")
sys.exit(1 if bad else 0)
PY
