#!/usr/bin/env bash
# Build a standalone driver for MAME's SPC700 disassembler (same text as unidasm -arch spc700)
# with fixed-stride and address-list modes, used as the decode oracle.
# MAME's sources (BSD-3-Clause) are fetched at tag mame0285 and checked by SHA-256.
#   test/build-mame-dis.sh <outdir>      -> <outdir>/mamespc700dis
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=$(mkdir -p "${1:?usage: build-mame-dis.sh <outdir>}" && cd "$1" && pwd)
SRC=$OUT/mame-src
mkdir -p "$SRC"
TAG=mame0285
fetch() { # path sha256
	local f=$SRC/$(basename "$1")
	[[ -f $f ]] || curl -sfL -o "$f" "https://raw.githubusercontent.com/mamedev/mame/$TAG/$1"
	echo "$2  $f" | sha256sum -c --quiet -
}
fetch src/devices/cpu/spc700/spc700ds.cpp 4950a6435de5253b4c194947302409466925651fd8d6dac416754db13ad01a8c
fetch src/devices/cpu/spc700/spc700ds.h f40b274635e56a65d3f5e2d45b910cb9e546ca48e42517d2e683f1ccbe9eaec1
fetch src/lib/util/disasmintf.h 66ca50e7a31e9371c922a879c34b7ad0e02373b08b48dcd129c1470c611098bc
fetch src/lib/util/disasmintf.cpp 02e6e57df15e39ad195a21400df3703b8cd06808502c10b7ef140df8ad262fd4
# Minimal stand-ins for MAME's emu.h / osdcomm.h / strformat.h.
cat > "$SRC/osdcomm.h" <<'H'
#pragma once
#include <cstdint>
namespace osd { using u8=uint8_t; using u16=uint16_t; using u32=uint32_t; using u64=uint64_t;
  using s8=int8_t; using s16=int16_t; using s32=int32_t; using s64=int64_t; }
H
cat > "$SRC/emu.h" <<'H'
#pragma once
#include <cstdio>
#include <string>
#include <ostream>
#include "osdcomm.h"
#include "disasmintf.h"
using osd::u8; using osd::u16; using osd::u32; using osd::u64; using offs_t = uint32_t;
namespace util {
template <typename T> static inline T conv(T v) { return v; }
static inline const char *conv(const std::string &s) { return s.c_str(); }
template <typename... A> std::string string_format(const char *f, A&&... a) {
  char b[256]; snprintf(b, sizeof b, f, conv(a)...); return b; }
template <typename... A> void stream_format(std::ostream &o, const char *f, A&&... a) {
  char b[256]; snprintf(b, sizeof b, f, conv(a)...); o << b; }
}
H
c++ -std=c++17 -O2 -w -I"$SRC" -include "$SRC/emu.h" -o "$OUT/mamespc700dis" \
	"$HERE/mame_dis_main.cpp" "$SRC/spc700ds.cpp" "$SRC/disasmintf.cpp"
echo "built $OUT/mamespc700dis"
