// P-code emulation test for the SPC700 module: runs every case of emu/emu_cases.txt with
// EmulatorHelper and compares registers and memory with hand-computed results.
// Script args: <cases.txt> <labels.lbl> <outfile>
//@category Testing

import java.io.PrintStream;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;

import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.emulator.EmulatorHelper;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.lang.Register;
import ghidra.program.model.lang.RegisterValue;

public class SpcEmuTest extends GhidraScript {

	private Map<String, Long> labels = new HashMap<>();

	private long value(String v) {
		if (v.startsWith("@")) {
			return labels.get(v.substring(1));
		}
		return Long.parseLong(v, 16);
	}

	private byte[] bytes(String kind, String v) {
		if (kind.equals("mem16")) {
			long x = value(v);
			return new byte[] { (byte) x, (byte) (x >> 8) };
		}
		byte[] b = new byte[v.length() / 2];
		for (int i = 0; i < b.length; i++) {
			b[i] = (byte) Integer.parseInt(v.substring(2 * i, 2 * i + 2), 16);
		}
		return b;
	}

	@Override
	protected void run() throws Exception {
		String[] args = getScriptArgs();
		for (String l : Files.readAllLines(Path.of(args[1]))) {
			String[] p = l.trim().split("\\s+");
			if (p.length == 2) {
				labels.put(p[0], Long.parseLong(p[1], 16));
			}
		}
		PrintStream out = new PrintStream(args[2]);
		var lang = currentProgram.getLanguage();
		Register ctxreg = lang.getContextBaseRegister();
		Register ctxP = lang.getRegister("ctx_P");
		String[] flags = { "CF", "ZF", "IF", "HF", "BF", "PF", "VF", "NF" };
		int pass = 0, fail = 0;
		for (String line : Files.readAllLines(Path.of(args[0]))) {
			if (line.isBlank() || line.startsWith("#")) {
				continue;
			}
			String[] f = line.split("\\|");
			String name = f[0].trim();
			int p = Integer.parseInt(f[1].trim());
			String[] init = f[3].trim().isEmpty() ? new String[0] : f[3].trim().split("\\s+");
			String[] expect = f[4].trim().isEmpty() ? new String[0] : f[4].trim().split("\\s+");
			Address start = toAddr(labels.get(name));
			RegisterValue rv = new RegisterValue(ctxreg).assign(ctxP, BigInteger.valueOf(p));
			clearListing(start, start.add(0x3f));
			DisassembleCommand cmd = new DisassembleCommand(start, null, true);
			cmd.setInitialContext(rv);
			cmd.applyTo(currentProgram, monitor);

			EmulatorHelper emu = new EmulatorHelper(currentProgram);
			StringBuilder why = new StringBuilder();
			try {
				emu.setContextRegister(rv);
				for (String fl : flags) {
					emu.writeRegister(fl, 0);
				}
				emu.writeRegister("PF", p);
				for (String r : new String[] { "A", "X", "Y" }) {
					emu.writeRegister(r, 0);
				}
				emu.writeRegister("SP", 0x1ef);
				for (String it : init) {
					String[] kv = it.split("=", 2);
					if (kv[0].contains(":")) {
						String[] ka = kv[0].split(":");
						emu.writeMemory(toAddr(Long.parseLong(ka[1], 16)), bytes(ka[0], kv[1]));
					}
					else {
						emu.writeRegister(kv[0], value(kv[1]));
					}
				}
				emu.writeRegister(lang.getProgramCounter(), start.getOffset());
				int steps = 0;
				while (steps++ < 500) {
					Address pc = emu.getExecutionAddress();
					if ((emu.readMemory(pc, 1)[0] & 0xff) == 0xff) {
						break; // STOP ends the case
					}
					try {
						emu.getEmulator().executeInstruction(true, monitor);
					}
					catch (Exception ex) {
						why.append(" emulation error at ").append(pc).append(": ").append(ex);
						break;
					}
				}
				for (String e : expect) {
					String[] kv = e.split("=", 2);
					if (kv[0].contains(":")) {
						String[] ka = kv[0].split(":");
						byte[] want = bytes(ka[0], kv[1]);
						byte[] got = emu.readMemory(toAddr(Long.parseLong(ka[1], 16)), want.length);
						if (!Arrays.equals(want, got)) {
							why.append(String.format(" %s: want %s got %s", kv[0], hex(want), hex(got)));
						}
					}
					else {
						long want = value(kv[1]);
						long got = emu.readRegister(kv[0]).longValue();
						if (want != got) {
							why.append(String.format(" %s: want %x got %x", kv[0], want, got));
						}
					}
				}
			}
			catch (Exception ex) {
				why.append(" exception: ").append(ex);
			}
			finally {
				emu.dispose();
			}
			if (why.length() == 0) {
				pass++;
				out.println("PASS " + name);
			}
			else {
				fail++;
				out.println("FAIL " + name + why);
			}
		}
		out.printf("emulator: %d passed, %d failed%n", pass, fail);
		out.close();
	}

	private static String hex(byte[] b) {
		StringBuilder s = new StringBuilder();
		for (byte x : b) {
			s.append(String.format("%02x", x & 0xff));
		}
		return s.toString();
	}
}
