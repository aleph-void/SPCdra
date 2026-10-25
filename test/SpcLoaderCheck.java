// SPC loader check (test/loader-test.sh): print the DSP overlay block, the KON register byte and
// label, and the entry point instruction.   Script args: <outfile>
//@category Testing

import java.io.PrintStream;

import ghidra.app.script.GhidraScript;

public class SpcLoaderCheck extends GhidraScript {

	@Override
	protected void run() throws Exception {
		PrintStream out = new PrintStream(getScriptArgs()[0]);
		var dsp = currentProgram.getMemory().getBlock("DSP");
		out.println("dspblock " + (dsp == null ? "none" : dsp.getStart() + " " + dsp.getSize() +
			" overlay=" + dsp.isOverlay()));
		if (dsp != null) {
			var kon = dsp.getStart().add(0x4c);
			out.printf("kon %02x %s%n", currentProgram.getMemory().getByte(kon) & 0xff,
				getSymbolAt(kon));
			var v3 = dsp.getStart().add(0x34);
			out.printf("v3srcn %02x %s%n", currentProgram.getMemory().getByte(v3) & 0xff,
				getSymbolAt(v3));
		}
		for (var a : currentProgram.getSymbolTable().getExternalEntryPointIterator()) {
			out.println("entry " + a + " " + getInstructionAt(a));
		}
		out.close();
	}
}
