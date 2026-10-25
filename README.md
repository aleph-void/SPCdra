> **Ghidra-Rare fork.** This branch adds tested fixes, release builds for the three newest Ghidra
> releases and test suites; see [GHIDRA-RARE.md](GHIDRA-RARE.md) for what was verified and how,
> and [CREDITS.md](CREDITS.md) for every change. Prebuilt extension zips are on the
> [Releases page](https://github.com/aleph-void/SPCdra/releases). The original README follows;
> text this fork made wrong is updated in place and marked *(fork)*.

# SPCdra: SPC700 loader for Ghidra

[![Sponsor Aleph Void](https://img.shields.io/badge/Sponsor-Aleph%20Void-EA4AAA?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/aleph-void)


~~**Very experimental! No compatibility guarantees.**~~ *(fork)* Verified: every opcode against
MAME's SPC700 disassembler and the bass assembler, all 256,000 SingleStepTests/spc700 cases
(255,995 pass; the 5 others are instructions whose bytes run past `$FFFF`, see GHIDRA-RARE.md)
and the SNESMOD driver with MAME execution traces, on Ghidra 12.1.3, 12.1.4 and 12.2.

## Features
* Sony/Nintendo SPC700 APU support for Sleigh
* SPC file loader
* Symbols for hardware registers
* *(fork)* the 128 S-DSP registers of a `.spc` file as the overlay block `DSP`, with their names
* *(fork)* two syntaxes: Sony mnemonics (`spc700:LE:16:default`) and 65816-style
  (`spc700:LE:16:65816`)
* Processor manual index (manual available from [The Internet Archive](https://archive.org/details/SNESDevManual))

## How to install
*(fork)* Download the zip for your Ghidra version from the
[Releases page](https://github.com/aleph-void/SPCdra/releases).

1. Start Ghidra
2. File -> Install Extensions
3. Press the '+' icon ("Add extension")
4. Choose the built or downloaded SPCdra zip file
5. Restart Ghidra when prompted to load the extension properly

## Loading files
1. Start Ghidra
2. Create a new project
3. File -> Import File
4. Select the .spc file you want to load
5. Click Options...
6. Type the main entrypoint address for the SPC engine (see below for details)
7. Click OK

## Finding the SPC engine entrypoint address
Finding the actual entrypoint for a given .spc file is important, because without it, it will be difficult to determine where to begin disassembly and analysis.  By default, the loader will use the PC address stored in the .spc file metadata, but this is typically not going to be the actual entrypoint, but rather, whatever instruction the SPC was executing when the file was dumped.  To find the actual entrypoint, you will need [bsnes+](https://github.com/devinacker/bsnes-plus/releases/latest) as well as the game ROM that the .spc file was dumped from.

*(fork)* This is still needed: a `.spc` file does not record where the boot ROM started the
driver. The boot ROM leaves that address in `$0000-$0001`, but drivers overwrite it (SNESMOD
clears page 0 first thing), and there is no common driver prologue to search for (SNESMOD does not
set the stack pointer). On the three MAME-dumped SNESMOD snapshots in the test suite, neither the
`$0000` word nor a `MOV X,#imm; MOV SP,X` scan finds the real entry `$0400`, so the loader does
not guess; see [GHIDRA-RARE.md](GHIDRA-RARE.md). The saved PC still gives a useful start (usually
the driver's main loop).

1. Start bsnes+
2. Tools -> Debugger
3. (In the Debugger window) Click "Break"
4. (In the Main window) System -> Load Cartridge . . . -> Select game ROM
5. (In the Debugger window) Tools -> Breakpoint Editor
6. (In the Breakpoint window) Click "Add"
7. Double-click the empty cell under "End (optional)" and type "fbff"
8. Check the box under 'X'
9. Under "Source", select "S-SMP bus"

![Breakpoint Window](src/main/resources/images/bsnes_entrypoint_breakpoint.png) 

10. (In the Debugger window) Click "Run" 
11. Once the breakpoint is hit, the address of the current instruction is the entrypoint address

![Debugger Window](src/main/resources/images/bsnes_entrypoint_debugger.png) 

## License
Licensed under the Apache License, Version 2.0