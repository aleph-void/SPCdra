#!/usr/bin/env bash
# Fetch freely licensed SPC700 code for the real-binary test (never committed).
#   test/fetch-real-samples.sh <dir>
# Sources (pinned by SHA-256):
#   SNESMOD sound driver as shipped in PVSnesLib 4.6.0 (github.com/alekmaul/pvsneslib, MIT):
#     pvsneslib/source/sm_spc.asm -> roms/snesmod.bin (raw, loads at $0400) and
#     roms/snesmod.spc (snapshot for the SPC loader, PC = $0400)
#   PVSnesLib 4.6.0 example ROMs that play music through that driver (for MAME traces)
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
DIR=$(mkdir -p "${1:?usage: fetch-real-samples.sh <dir>}" && cd "$1" && pwd)
cd "$DIR"
get() { # url sha256 file
	[[ -f $3 ]] || curl -sfL -o "$3" "$1"
	echo "$2  $3" | sha256sum -c --quiet -
}
get https://raw.githubusercontent.com/alekmaul/pvsneslib/4.6.0/pvsneslib/source/sm_spc.asm \
	3ab9c1bd2ab5cc59626ba01586fde45559f4f5ef8afd4ab7515671a738b0449d sm_spc.asm
get https://github.com/alekmaul/pvsneslib/releases/download/4.6.0/pvsneslib_460_64b_linux_release.zip \
	db08f2f95400125f8ae0cc62e87c3c350fa46a3eadb3174dd3161606ee49c84c pvsneslib-4.6.0.zip
mkdir -p roms snes
python3 "$HERE/make_spc.py" driver sm_spc.asm roms/snesmod.bin roms/snesmod.spc >/dev/null
while read -r sha path; do
	out=snes/$(basename "$path")
	[[ -f $out ]] || unzip -p pvsneslib-4.6.0.zip "$path" > "$out"
	echo "$sha  $out" | sha256sum -c --quiet -
done <<'LIST'
86f8773c4db36340fb4cdb2a6edf24cb1b6af135e5f18fa9c395df43ca93675d pvsneslib/snes-examples/audio/music/music.sfc
6ecf32a4537ac46587df5896135683d533c6c743c46288a3b634bc9a717e6f36 pvsneslib/snes-examples/audio/musicHiROM/musicHiROM.sfc
cad5126ac19cc7729a274ae1f1342a51d6086b172b55d5a76f2e2fe7e23cdadf pvsneslib/snes-examples/systems/games/likemario/likemario.sfc
LIST
ls "$DIR"/roms "$DIR"/snes
