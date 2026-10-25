// Runs SingleStepTests/spc700 cases (initial CPU/RAM state -> one instruction -> final state)
// through Ghidra's p-code emulator and reports agreement per opcode.
// Script args: <tests.json> <outfile>
// Compared: PC, A, X, Y, SP, PSW (all eight flags) and every RAM byte in the final state.
// PSW.P also selects the decode context (ctx_P) for direct-page operands.
//@category Testing

import java.io.FileReader;
import java.io.PrintStream;
import java.math.BigInteger;
import java.util.*;

import com.google.gson.*;

import ghidra.app.emulator.EmulatorHelper;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.lang.Register;
import ghidra.program.model.lang.RegisterValue;

public class SpcSingleStep extends GhidraScript {

	private static final String[] FLAGS = { "CF", "ZF", "IF", "HF", "BF", "PF", "VF", "NF" };

	@Override
	protected void run() throws Exception {
		String[] args = getScriptArgs();
		JsonArray tests = JsonParser.parseReader(new FileReader(args[0])).getAsJsonArray();
		PrintStream out = new PrintStream(args[1]);
		var lang = currentProgram.getLanguage();
		Register ctx = lang.getContextBaseRegister();
		Register ctxP = lang.getRegister("ctx_P");
		Map<String, int[]> perOp = new TreeMap<>();
		Map<String, String> firstFail = new TreeMap<>();
		int pass = 0, fail = 0;
		for (JsonElement el : tests) {
			JsonObject t = el.getAsJsonObject();
			String name = t.get("name").getAsString();
			JsonObject in = t.getAsJsonObject("initial"), fin = t.getAsJsonObject("final");
			String key = name.substring(0, 2).toLowerCase();
			int psw = in.get("psw").getAsInt();
			EmulatorHelper emu = new EmulatorHelper(currentProgram);
			String why = null;
			try {
				RegisterValue rv = new RegisterValue(ctx);
				rv = rv.assign(ctxP, BigInteger.valueOf((psw >> 5) & 1));
				emu.setContextRegister(rv);
				emu.writeRegister("A", in.get("a").getAsInt());
				emu.writeRegister("X", in.get("x").getAsInt());
				emu.writeRegister("Y", in.get("y").getAsInt());
				emu.writeRegister("SP", 0x100 | in.get("sp").getAsInt());
				for (int b = 0; b < 8; b++) {
					emu.writeRegister(FLAGS[b], (psw >> b) & 1);
				}
				for (JsonElement m : in.getAsJsonArray("ram")) {
					JsonArray kv = m.getAsJsonArray();
					emu.writeMemory(toAddr(kv.get(0).getAsLong()),
						new byte[] { (byte) kv.get(1).getAsInt() });
				}
				emu.writeRegister(lang.getProgramCounter(), in.get("pc").getAsLong());
				emu.getEmulator().executeInstruction(true, monitor);
				StringBuilder d = new StringBuilder();
				long gpc = emu.readRegister(lang.getProgramCounter()).longValue();
				if (gpc != fin.get("pc").getAsLong()) {
					d.append(String.format(" PC %04x!=%04x", gpc, fin.get("pc").getAsLong()));
				}
				for (String r : new String[] { "a", "x", "y" }) {
					long g = emu.readRegister(r.toUpperCase()).longValue();
					if (g != fin.get(r).getAsLong()) {
						d.append(String.format(" %s %02x!=%02x", r, g, fin.get(r).getAsLong()));
					}
				}
				long gsp = emu.readRegister("SP").longValue();
				if (gsp != (0x100 | fin.get("sp").getAsLong())) {
					d.append(String.format(" SP %x!=1%02x", gsp, fin.get("sp").getAsLong()));
				}
				int fp = fin.get("psw").getAsInt();
				for (int b = 0; b < 8; b++) {
					long g = emu.readRegister(FLAGS[b]).longValue();
					if (g != ((fp >> b) & 1)) {
						d.append(String.format(" %s %d!=%d", FLAGS[b], g, (fp >> b) & 1));
					}
				}
				for (JsonElement m : fin.getAsJsonArray("ram")) {
					JsonArray kv = m.getAsJsonArray();
					byte[] g = emu.readMemory(toAddr(kv.get(0).getAsLong()), 1);
					if ((g[0] & 0xff) != kv.get(1).getAsInt()) {
						d.append(String.format(" mem[%04x] %02x!=%02x", kv.get(0).getAsLong(),
							g[0] & 0xff, kv.get(1).getAsInt()));
					}
				}
				if (d.length() > 0) {
					why = d.toString();
				}
			}
			catch (Exception ex) {
				why = " exception " + ex;
			}
			finally {
				emu.dispose();
			}
			int[] c = perOp.computeIfAbsent(key, k -> new int[2]);
			if (why == null) {
				c[0]++;
				pass++;
			}
			else {
				c[1]++;
				fail++;
				firstFail.putIfAbsent(key, name + ":" + why);
			}
		}
		for (var en : perOp.entrySet()) {
			int[] c = en.getValue();
			out.printf("%s %d/%d%s%n", en.getKey(), c[0], c[0] + c[1],
				c[1] > 0 ? "  e.g. " + firstFail.get(en.getKey()) : "");
		}
		out.printf("singlestep: %d passed, %d failed (%d of %d opcodes fully passing)%n", pass, fail,
			perOp.values().stream().filter(c -> c[1] == 0).count(), perOp.size());
		out.close();
	}
}
