# Credits: Sony SPC700

## Upstream

- Repository: https://github.com/qwertymodo/SPCdra
- Commit: `295b552f768eb23abf601c46e27a6d5d3e10a03b` (2026-03-04, "Update load and
  getDefaultOptions signatures for Ghidra v12 API")
- License: Apache-2.0 (`LICENSE`)
- Original author: **qwertymodo** ([@qwertymodo](https://github.com/qwertymodo),
  `<qwertymodo@qwertymodo.com>`), all 13 commits. No other implementation was found.

The two language variants come from upstream: `spc700:LE:16:default` uses Sony's mnemonics
(`MOV A,dp`) and `spc700:LE:16:65816` uses 65816-style mnemonics (`LDA dp`), the syntax of
`data/languages/spc700.arch`. That file is the `spc700` table of the bass assembler (byuu/near,
as maintained in [ARM9/bass](https://github.com/ARM9/bass)) and is identical to bass's own
`data/architectures/spc700.arch` apart from the first line. It is the same CPU and the same
language; only the display text differs.

## What Ghidra-Rare changed

Each change is a commit on branch `ghidra-rare` of the fork of qwertymodo/SPCdra (Ghidra-Rare
includes the fork as a submodule).

1. **Generated SLEIGH, fixed decoding and p-code** (`c1f1ac7`). `tools/gen_spc700.py` now
   writes both `.slaspec` files from one 256-entry opcode table, so they share identical p-code.
   The 65816-style display follows `spc700.arch` exactly.
   - Decoding: the absolute-bit instructions (`OR1`/`AND1`/`EOR1`/`MOV1`/`NOT1` m.b) read their
     16-bit operand as two bytes. The operand is a 13-bit address plus a 3-bit bit number.
   - Direct page honours PSW.P through a `ctx_P` decode context set by `SETP`/`CLRP`.
   - `JMP`/`CALL !abs` and `PCALL` are direct flows.
   - P-code: the direct-page operand exported the memory *at* the address, so every
     direct-page access dereferenced twice. `MOV dp,X/Y` added X. Shifts on `dp+X` stored the
     pointer. Indexed direct page did not wrap within the page. The stack was in page 0 with
     pre-decrement, and `CALL`/`PCALL`/`TCALL` pushed nothing. The `TCALL` and `BRK` vectors were
     wrong.
   - Flags: `ADC` cleared N and never set V; INC/DEC and the 16-bit ops set no flags; shifts
     always cleared C; MUL, DIV and DAA/DAS were missing or pcodeops.
   - Flags are now separate registers that `PUSH`/`POP PSW`, `BRK` and `RETI` pack and unpack.
     The cspec stack grows down with the return address at SP+1, and `$F0-$FF` are volatile.
2. **SPC loader** (`36f07e8`): entry points at `$8000` and above were wrong because a byte was
   sign-extended. The entry is now decoded with the saved PSW's direct page, `$FC`/`$FF` are
   named TIMER2/COUNTER2, and only the native-syntax language is preferred.

3. **SLEEP/STOP** (`e308242`): halt as a self-loop instead of `sleep()`/`stop()` pcodeops, which
   stopped Ghidra's emulator.
4. **PSW.P through PUSH PSW ... POP PSW** (`4d14cac`): POP PSW restores the direct-page decode
   context saved by the PUSH PSW on the same flow path.
5. **Return address in 16 bits** (`e2c00b6`): CALL/PCALL/TCALL/BRK push `inst_start + length`,
   so a TCALL/BRK at `$FFFF` returns to `$0000` instead of failing.
6. **Tests for upstream issues #1 and #2** (`0b50b41`): JMP `[!a+X]` and INC/DEC flag cases (both
   bugs were fixed by change 1).
7. **SPC loader** (`cae8ae7`): the 128 S-DSP registers as the overlay block `DSP` with register
   names; class documentation and entry-address validation (upstream TODOs).
8. **README** (this commit series): the "very experimental" warning, install from the Releases
   page, and why the entry point is still not found automatically.

The Ghidra-Rare additions (`GHIDRA-RARE.md`, `CREDITS.md`, `test/`, `build.gradle`,
`extension.properties`, the release workflow) are in the fork too (`4891483`, `baea358`).

## Test inputs and tools (not redistributed)

- MAME `spc700` disassembler (`src/devices/cpu/spc700/spc700ds.cpp`, BSD-3-Clause, Karl
  Stenerud) at tag `mame0285`, built by `test/build-mame-dis.sh`.
- bass assembler ([ARM9/bass](https://github.com/ARM9/bass), commit `c3962ec`) for the
  65816-style round trip and the emulator test program.
- [SingleStepTests/spc700](https://github.com/SingleStepTests/spc700) (MIT), commit `67d15f4`.
- The SNESMOD sound driver as shipped in PVSnesLib 4.6.0
  ([alekmaul/pvsneslib](https://github.com/alekmaul/pvsneslib), MIT; SNESMOD by Mukunda
  Johnson), plus PVSnesLib example ROMs run in MAME, fetched by `test/fetch-real-samples.sh`.
