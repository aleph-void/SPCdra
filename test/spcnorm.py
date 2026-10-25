"""Text normalisation for comparing Ghidra's SPC700 (native syntax) with MAME's spc700 text."""
import re


def _hex(m):
    return "$%x" % int(m.group(1), 16)


def norm_ghidra(t):
    t = t.strip().lower()
    t = re.sub(r"\s+", " ", t)
    t = t.replace("!", "")                       # absolute-address marker
    t = t.replace("[", "(").replace("]", ")")    # indirect
    t = re.sub(r"0x([0-9a-f]+)", _hex, t)
    m = re.fullmatch(r"tcall \$([0-9a-f]+)", t)
    if m:
        t = "tcall %d" % int(m.group(1), 16)
    # bit operands: "$12.$3" -> "$12.3"
    t = re.sub(r"\.\$([0-7])\b", r".\1", t)
    # BBS/BBC "dp,bit,target" -> "dp.bit,target"
    t = re.sub(r"^(bbs|bbc) (\$[0-9a-f]+),\$([0-7]),", r"\1 \2.\3,", t)
    return t


def norm_mame(t):
    t = t.strip().lower()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\$([0-9a-f]+)", _hex, t)
    # bare 4-digit branch targets and mem.bit addresses ("0043", "1412.1")
    t = re.sub(r"(?<![$\w])([0-9a-f]{4})\b", lambda m: "$%x" % int(m.group(1), 16), t)
    return t


def semantic(g, m, op):
    """Fold spelling differences that do not change meaning."""
    if op == 0xdf and m == "daa" and g == "daa a":
        return True
    if op in (0x5a, 0x7a, 0x9a):                 # MAME drops the implied YA of CMPW/ADDW/SUBW
        m = re.sub(r"^(\w+) ", r"\1 ya,", m)
    return g == m


def mame_not1_bug(gbytes, gtext):
    """MAME's spc700 disassembler decodes NOT1 m.b ($EA) as a 1-byte instruction although its
    own CPU core (OP_NOT1) reads a 16-bit operand. Check Ghidra's text against the encoding."""
    if len(gbytes) != 6 or not gbytes.startswith("ea"):
        return False
    w = int(gbytes[4:6] + gbytes[2:4], 16)
    return norm_ghidra(gtext) == "not1 $%x.%d" % (w & 0x1fff, w >> 13)
