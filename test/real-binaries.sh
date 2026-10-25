#!/usr/bin/env bash
# Real-binary test for the SPC700 module.
#   test/real-binaries.sh <samples-dir> <workdir> <mamespc700dis> [seconds]
# 1. snesmod.spc: SNESMOD driver from PVSnesLib's source tree, imported with the SPC loader.
# 2. If MAME is installed: each PVSnesLib music ROM runs in MAME's snes driver (with the
#    independent boot ROM from trace/make_ipl.py) while the SPC700 is traced; after 5 s the
#    SPC700 RAM and registers are saved as a .spc (as real-world .spc dumps are made, with the
#    PC set to the driver entry $0400) and imported with the SPC loader. Every listing is re-decoded by MAME and compared with the
#    union of the execution traces.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
SAMPLES=$(mkdir -p "$1" && cd "$1" && pwd); WORK=$(mkdir -p "$2" && cd "$2" && pwd); DIS=$3
SECS=${4:-10}
"$HERE/fetch-real-samples.sh" "$SAMPLES" >/dev/null
spcs=("$SAMPLES/roms/snesmod.spc")
traces=()
if command -v mame >/dev/null; then
	python3 "$HERE/trace/make_ipl.py" "$WORK/mame-roms" >/dev/null
	for rom in "$SAMPLES"/snes/*.sfc; do
		name=$(basename "$rom" .sfc)
		cat > "$WORK/$name.lua" <<LUA
local d = manager.machine.debugger
d:command("trace $WORK/$name.trace,:soundcpu,noloop")
d:command("go")
local frames = 0
dump_sub = emu.add_machine_frame_notifier(function()
  frames = frames + 1
  if frames == 300 then
    local cpu = manager.machine.devices[":soundcpu"]
    local sp = cpu.spaces["program"]
    local f = io.open("$WORK/$name.ram", "wb")
    for a = 0, 0xffff do f:write(string.char(sp:read_u8(a))) end
    f:close()
    local s = cpu.state
    f = io.open("$WORK/$name.regs", "w")
    f:write(string.format("%d %d %d %d %d %d", s["PC"].value, s["A"].value, s["X"].value,
      s["Y"].value, s["P"].value, s["S"].value))
    f:close()
  end
end)
LUA
		timeout 600 mame snes -rompath "$WORK/mame-roms" -cart "$rom" -debug -debugger none \
			-autoboot_script "$WORK/$name.lua" -autoboot_delay 0 -video none -sound none \
			-nothrottle -seconds_to_run "$SECS" -skip_gameinfo >/dev/null 2>&1 || true
		rm -f "$WORK/$name.lua"
		if [[ -s $WORK/$name.trace ]]; then
			sort -u -o "$WORK/$name.trace" "$WORK/$name.trace"
			traces+=(--trace "$WORK/$name.trace")
		fi
		if [[ -s $WORK/$name.ram && -s $WORK/$name.regs ]]; then
			# The saved PC is wherever the driver was (as in real .spc dumps, see the SPCdra README);
			# use the driver's entry point $0400 instead, as a user would via the loader option.
			read -r _pc a x y p s < "$WORK/$name.regs" || true
			python3 "$HERE/make_spc.py" dump "$WORK/$name.ram" 1024 "$a" "$x" "$y" "$p" "$s" "$WORK/$name-mame.spc"
			spcs+=("$WORK/$name-mame.spc")
		fi
	done
fi
for spc in "${spcs[@]}"; do
	name=$(basename "$spc" .spc)
	"$HERE/real-check.sh" "$spc" "$WORK/$name"
	echo "== $name: $(sed -n 2p "$WORK/$name.summary") [$(grep -o 'Using Loader: [^(]*' "$WORK/$name.import" | sed 's/ *$//')]"
	python3 "$HERE/real_compare.py" "$WORK/$name.lst" "$DIS" "${traces[@]}" --label "$name"
done
