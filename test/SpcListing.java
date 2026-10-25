// Flow-disassemble a raw SPC700 image from an entry point with an initial PSW.P decode context and
// dump the listing with each instruction's ctx_P (used by test/ctx-test.sh).
// Script args: <outfile> <entry-hex> <P>
//@category Testing

import java.io.PrintStream;
import java.math.BigInteger;

import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.lang.Register;
import ghidra.program.model.lang.RegisterValue;
import ghidra.program.model.listing.Instruction;

public class SpcListing extends GhidraScript {

	@Override
	protected void run() throws Exception {
		String[] args = getScriptArgs();
		PrintStream out = new PrintStream(args[0]);
		Register ctx = currentProgram.getLanguage().getContextBaseRegister();
		Register p = currentProgram.getLanguage().getRegister("ctx_P");
		DisassembleCommand cmd = new DisassembleCommand(toAddr(Long.parseLong(args[1], 16)), null,
			true);
		cmd.setInitialContext(new RegisterValue(ctx).assign(p, new BigInteger(args[2])));
		cmd.applyTo(currentProgram, monitor);
		for (Instruction ins : currentProgram.getListing().getInstructions(true)) {
			out.printf("%04x P%s %s%n", ins.getAddress().getOffset(), ins.getValue(p, false), ins);
		}
		out.close();
	}
}
