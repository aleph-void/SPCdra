/* ###
 * IP: GHIDRA
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *      http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package spcdra;

import java.io.IOException;
import java.util.*;

import ghidra.app.util.MemoryBlockUtils;
import ghidra.app.util.Option;
import ghidra.app.util.OptionUtils;
import ghidra.app.util.bin.ByteProvider;
import ghidra.app.util.importer.MessageLog;
import ghidra.app.util.opinion.AbstractLibrarySupportLoader;
import ghidra.app.util.opinion.LoadSpec;
import ghidra.framework.model.DomainObject;
import ghidra.program.model.address.AddressOutOfBoundsException;
import ghidra.program.model.address.AddressOverflowException;
import ghidra.program.model.lang.LanguageCompilerSpecPair;
import ghidra.program.model.listing.Program;
import ghidra.program.model.symbol.SourceType;
import ghidra.util.exception.CancelledException;
import ghidra.util.exception.InvalidInputException;
import ghidra.util.task.TaskMonitor;

import static ghidra.app.util.MemoryBlockUtils.createInitializedBlock;

/**
 * Loads an SPC700 sound snapshot (.spc, "SNES-SPC700 Sound File Data v0.30"): the 64 KB of
 * SPC700 RAM at $0000, the 128 S-DSP registers (reached by the CPU only through the $F2/$F3
 * address/data window) as the overlay block "DSP" with the register names, labels for the I/O
 * registers at $F0-$FF, and an entry point at the "Entrypoint Address" option (default: the
 * snapshot's saved PC), decoded with the direct page the saved PSW selects.
 * <p>
 * The saved PC is wherever the sound driver was when the snapshot was taken (usually its main
 * loop), not where the boot ROM started it. A .spc file does not record that address: the IPL
 * leaves it in $0000-$0001, which drivers overwrite (SNESMOD clears page 0 first thing), so the
 * real entry still has to be found by hand (see the help page).
 */
public class SPCLoader extends AbstractLibrarySupportLoader {
	private static final String OPT_EP_ADDRESS = "Entrypoint Address";

	@Override
	public String getName() {

		return "SPC700";
	}

	@Override
	public Collection<LoadSpec> findSupportedLoadSpecs(ByteProvider provider) throws IOException {
		List<LoadSpec> loadSpecs = new ArrayList<>();
		
		try {
			if(new String(provider.getInputStream(0).readNBytes(33),0,33).compareTo("SNES-SPC700 Sound File Data v0.30") != 0)
				return loadSpecs;
			
			loadSpecs.add(new LoadSpec(this, 0, new LanguageCompilerSpecPair("spc700:LE:16:default", "default"), true));
			// The 65816-style variant is the same language with other mnemonics: offered, not
			// preferred, so a headless import picks one language.
			loadSpecs.add(new LoadSpec(this, 0, new LanguageCompilerSpecPair("spc700:LE:16:65816", "default"), false));
		} catch(IllegalArgumentException e) {}
		
		return loadSpecs;
	}

	@Override
	protected void load(Program program, ImporterSettings settings)
			throws CancelledException, IOException {
		
		var as = program.getAddressFactory().getDefaultAddressSpace();
		var spc = MemoryBlockUtils.createFileBytes(program, settings.provider(), settings.monitor());

		try {
			createInitializedBlock(program, false, "ram", as.getAddress(0x0000), spc, 0x100, 0x10000, "", "", true, true, true, settings.log());
			var st = program.getSymbolTable();
			st.createLabel(as.getAddress(0xF0), "TEST_REGISTER", SourceType.IMPORTED);
			st.createLabel(as.getAddress(0xF1), "CONTROL_REGISTER", SourceType.IMPORTED);
			st.createLabel(as.getAddress(0xF2), "DSP_ADDRESS_REGISTER", SourceType.IMPORTED);
			st.createLabel(as.getAddress(0xF3), "DSP_DATA_REGISTER", SourceType.IMPORTED);
			st.createLabel(as.getAddress(0xF4), "PORT0", SourceType.IMPORTED);
			st.createLabel(as.getAddress(0xF5), "PORT1", SourceType.IMPORTED);
			st.createLabel(as.getAddress(0xF6), "PORT2", SourceType.IMPORTED);
			st.createLabel(as.getAddress(0xF7), "PORT3", SourceType.IMPORTED);
			st.createLabel(as.getAddress(0xFA), "TIMER0", SourceType.IMPORTED);
			st.createLabel(as.getAddress(0xFB), "TIMER1", SourceType.IMPORTED);
			st.createLabel(as.getAddress(0xFC), "TIMER2", SourceType.IMPORTED);
			st.createLabel(as.getAddress(0xFD), "COUNTER0", SourceType.IMPORTED);
			st.createLabel(as.getAddress(0xFE), "COUNTER1", SourceType.IMPORTED);
			st.createLabel(as.getAddress(0xFF), "COUNTER2", SourceType.IMPORTED);
			st.createLabel(as.getAddress(0xFFC0), "IPL", SourceType.IMPORTED);

			// S-DSP registers (file offset $10100), reached through $F2 (address) / $F3 (data)
			if (settings.provider().length() >= 0x10180) {
				var dsp = createInitializedBlock(program, true, "DSP", as.getAddress(0), spc,
					0x10100, 0x80, "S-DSP registers ($F2/$F3 window)", "", true, true, false,
					settings.log());
				var ds = dsp.getStart().getAddressSpace();
				String[] voice = { "VOLL", "VOLR", "PITCHL", "PITCHH", "SRCN", "ADSR1", "ADSR2",
					"GAIN", "ENVX", "OUTX" };
				String[][] global = { { "MVOLL", "0C" }, { "MVOLR", "1C" }, { "EVOLL", "2C" },
					{ "EVOLR", "3C" }, { "KON", "4C" }, { "KOFF", "5C" }, { "FLG", "6C" },
					{ "ENDX", "7C" }, { "EFB", "0D" }, { "PMON", "2D" }, { "NON", "3D" },
					{ "EON", "4D" }, { "DIR", "5D" }, { "ESA", "6D" }, { "EDL", "7D" } };
				for (int v = 0; v < 8; v++) {
					for (int r = 0; r < voice.length; r++) {
						st.createLabel(ds.getAddress(v << 4 | r), "V" + v + voice[r],
							SourceType.IMPORTED);
					}
					st.createLabel(ds.getAddress(v << 4 | 0xF), "FIR" + v, SourceType.IMPORTED);
				}
				for (String[] g : global) {
					st.createLabel(ds.getAddress(Integer.parseInt(g[1], 16)), g[0],
						SourceType.IMPORTED);
				}
			}
			
			String op = OptionUtils.getOption(OPT_EP_ADDRESS, settings.options(), "0");
			int ep = Integer.parseInt(op.trim().replaceFirst("(?i)^0x", ""), 16);
			var epAddr = as.getAddress(ep);
			st.addExternalEntryPoint(epAddr);
			st.createLabel(epAddr, "ENTRY", SourceType.IMPORTED);
			// Decode the entry with the direct page the saved PSW selects (PSW.P, bit 5).
			int psw = settings.provider().readByte(0x2A) & 0xff;
			var ctx = program.getLanguage().getContextBaseRegister();
			var rv = new ghidra.program.model.lang.RegisterValue(ctx).assign(
				program.getLanguage().getRegister("ctx_P"),
				java.math.BigInteger.valueOf((psw >> 5) & 1));
			program.getProgramContext().setRegisterValue(epAddr, epAddr, rv);
		} catch (AddressOverflowException e) {
			e.printStackTrace();
		} catch (AddressOutOfBoundsException e) {
			e.printStackTrace();
		} catch (InvalidInputException e) {
			e.printStackTrace();
		} catch (ghidra.program.model.listing.ContextChangeException e) {
			e.printStackTrace();
		}
	}

	@Override
	public List<Option> getDefaultOptions(ByteProvider provider, LoadSpec loadSpec,
			DomainObject domainObject, boolean isLoadIntoProgram, boolean mirrorFsLayout) {
		List<Option> list =
			super.getDefaultOptions(provider, loadSpec, domainObject, isLoadIntoProgram, mirrorFsLayout);
		
		int ep = -1;
		try {
			var pc = provider.getInputStream(0x25).readNBytes(2);
			ep = (pc[0] & 0xFF) | (pc[1] & 0xFF) << 8;   // was sign-extended for PC >= $8000
			list.add(new Option(OPT_EP_ADDRESS, String.format("%04X", ep)));
		} catch (IOException e) {
			list.add(new Option(OPT_EP_ADDRESS, ""));
			e.printStackTrace();
		}

		return list;
	}

	@Override
	public String validateOptions(ByteProvider provider, LoadSpec loadSpec, List<Option> options, Program program) {
		for (Option o : options) {
			if (o.getName().equals(OPT_EP_ADDRESS)) {
				String v = String.valueOf(o.getValue()).trim();
				if (!v.matches("(?i)(0x)?[0-9a-f]{1,4}")) {
					return OPT_EP_ADDRESS + " must be a hex address from 0000 to FFFF";
				}
			}
		}
		return super.validateOptions(provider, loadSpec, options, program);
	}
}
