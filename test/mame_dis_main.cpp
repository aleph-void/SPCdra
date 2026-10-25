// Standalone driver for MAME's SPC700 disassembler (src/devices/cpu/spc700/spc700ds.cpp,
// BSD-3-Clause, Karl Stenerud). Same output as "unidasm -arch spc700", plus a fixed-stride
// corpus mode and an address-list mode.
//
//   mamespc700dis <file> [-basepc hex] [-stride n]
//   mamespc700dis -list <file>     lines "<addr-hex> <bytes-hex>": decode each one
// Output: "<pc-hex4> <bytes> <text>".
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <sstream>
#include <string>
#include <vector>
#include "emu.h"
#include "spc700ds.h"

struct buf : util::disasm_interface::data_buffer {
	const std::vector<uint8_t> &d; uint32_t base;
	buf(const std::vector<uint8_t> &v, uint32_t b) : d(v), base(b) {}
	uint8_t g(uint32_t pc) const { uint32_t o = (pc - base) & 0xffff; return o < d.size() ? d[o] : 0; }
	u8 r8(offs_t pc) const override { return g(pc); }
	u16 r16(offs_t pc) const override { return g(pc) | g(pc + 1) << 8; }
	u32 r32(offs_t pc) const override { return r16(pc) | uint32_t(r16(pc + 2)) << 16; }
	u64 r64(offs_t pc) const override { return r32(pc) | uint64_t(r32(pc + 4)) << 32; }
};

static std::string trim(std::string s) {
	while (!s.empty() && s.back() == ' ') s.pop_back();
	return s;
}

int main(int argc, char **argv) {
	spc700_disassembler dis;
	if (argc == 3 && !strcmp(argv[1], "-list")) {
		FILE *lf = fopen(argv[2], "r");
		if (!lf) { perror(argv[2]); return 1; }
		char line[256];
		while (fgets(line, sizeof line, lf)) {
			unsigned addr; char hex[64];
			if (sscanf(line, "%x %63s", &addr, hex) != 2) continue;
			std::vector<uint8_t> d;
			for (size_t k = 0; hex[k] && hex[k + 1]; k += 2) {
				unsigned v; sscanf(hex + k, "%2x", &v); d.push_back(v);
			}
			while (d.size() < 4) d.push_back(0);
			buf b(d, addr);
			std::ostringstream s;
			uint32_t len = dis.disassemble(s, addr, b, b) & util::disasm_interface::LENGTHMASK;
			printf("%04x ", addr);
			for (uint32_t k = 0; k < len; k++) printf("%02x", d[k]);
			printf(" %s\n", trim(s.str()).c_str());
		}
		return 0;
	}
	if (argc < 2) { fprintf(stderr, "usage: %s file [-basepc hex] [-stride n]\n", argv[0]); return 2; }
	uint32_t base = 0, stride = 0;
	for (int i = 2; i < argc; i++) {
		if (!strcmp(argv[i], "-basepc")) base = strtoul(argv[++i], nullptr, 16);
		else if (!strcmp(argv[i], "-stride")) stride = atoi(argv[++i]);
	}
	FILE *f = fopen(argv[1], "rb");
	if (!f) { perror(argv[1]); return 1; }
	std::vector<uint8_t> d; int ch;
	while ((ch = fgetc(f)) != EOF) d.push_back(ch);
	fclose(f);
	buf b(d, base);
	for (uint32_t off = 0; off < d.size();) {
		uint32_t pc = (base + off) & 0xffff;
		std::ostringstream s;
		uint32_t len = dis.disassemble(s, pc, b, b) & util::disasm_interface::LENGTHMASK;
		printf("%04x ", pc);
		for (uint32_t k = 0; k < len; k++) printf("%02x", b.g(pc + k));
		printf(" %s\n", trim(s.str()).c_str());
		off += stride ? stride : len;
	}
	return 0;
}
