// Fixed-stride disassembly dump for the SPC700 test harness (no analysis): decodes one
// instruction at the start of every <stride>-byte record.
// One line per record: "<address-hex4> <bytes-hex> <instruction text>"; with mode "pcode" the
// flow type and p-code ops follow, indented.
// Script args: <outfile> <stride> [mode]
//@category Testing

import java.io.PrintStream;

import ghidra.app.script.GhidraScript;
import ghidra.app.util.PseudoInstruction;
import ghidra.program.model.address.Address;
import ghidra.program.model.lang.InstructionPrototype;
import ghidra.program.model.lang.ProcessorContextImpl;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.mem.MemoryBufferImpl;
import ghidra.program.model.pcode.PcodeOp;

public class SpcDumpDisasm extends GhidraScript {

	@Override
	protected void run() throws Exception {
		String[] args = getScriptArgs();
		PrintStream out = new PrintStream(args[0]);
		int stride = Integer.parseInt(args[1]);
		boolean pcode = args.length > 2 && args[2].equals("pcode");
		var lang = currentProgram.getLanguage();
		for (MemoryBlock block : currentProgram.getMemory().getBlocks()) {
			if (!block.isInitialized()) {
				continue;
			}
			Address end = block.getEnd();
			for (Address a = block.getStart(); a.compareTo(end) <= 0; a = a.add(stride)) {
				String text;
				String hex;
				PseudoInstruction ins = null;
				try {
					ProcessorContextImpl ctx = new ProcessorContextImpl(lang);
					MemoryBufferImpl buf = new MemoryBufferImpl(currentProgram.getMemory(), a);
					InstructionPrototype p = lang.parse(buf, ctx, false);
					ins = new PseudoInstruction(currentProgram, a, p, buf, ctx);
					text = ins.toString();
					StringBuilder sb = new StringBuilder();
					for (byte b : ins.getBytes()) {
						sb.append(String.format("%02x", b & 0xff));
					}
					hex = sb.toString();
				}
				catch (Exception e) {
					text = "BAD (" + String.valueOf(e.getMessage()).split("\n")[0] + ")";
					hex = String.format("%02x", currentProgram.getMemory().getByte(a) & 0xff);
				}
				out.printf("%04x %s %s%n", a.getOffset(), hex, text);
				if (pcode && ins != null) {
					out.printf("    flow=%s%n", ins.getFlowType());
					for (PcodeOp op : ins.getPcode()) {
						out.printf("    %s%n", op);
					}
				}
				if (end.getOffset() - a.getOffset() < stride) {
					break;
				}
			}
		}
		out.close();
	}
}
