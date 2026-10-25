#!/usr/bin/env python3
"""Generate the two SPC700 SLEIGH specs from one opcode table.

  tools/gen_spc700.py <data/languages>

Writes spc700-native.slaspec (Sony mnemonics, as in the SNES development manual) and
spc700-65816.slaspec (65816-style mnemonics, the syntax of data/languages/spc700.arch, a bass
assembler table). Both share spc700.sinc and identical p-code: only the display text differs.
"""
import os
import re
import sys

OUT = sys.argv[1] if __name__ == "__main__" else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "languages")

# ---------------------------------------------------------------------------------------------
# Operand modes. Each opcode lists its operands in Sony (destination, source) order.
#   A X Y YA SP PSW C   registers
#   imm      #imm8                    dp      direct page          dpx/dpy  dp+X / dp+Y
#   abs      !abs                     absx/absy  !abs+X / !abs+Y
#   idx      [dp+X]                   idy     [dp]+Y
#   ix iy    (X) (Y)                  ixinc   (X)+
#   rel      branch target            membit/nmembit  m.b  /m.b (13-bit address, 3-bit bit)
#   dpbit    dp.bit (bit in opcode)   tcall   TCALL n             upage  PCALL u
#   iabsx    [!abs+X] (JMP)           dps     source dp of "dp,dp" forms (encoded first)
# ---------------------------------------------------------------------------------------------
T = {}


def op(code, mn, *modes):
    T[code] = (mn, list(modes))


ALU = {0x00: "OR", 0x20: "AND", 0x40: "EOR", 0x60: "CMP", 0x80: "ADC", 0xA0: "SBC"}
for base, mn in ALU.items():
    op(base + 0x04, mn, "A", "dp")
    op(base + 0x05, mn, "A", "abs")
    op(base + 0x06, mn, "A", "ix")
    op(base + 0x07, mn, "A", "idx")
    op(base + 0x08, mn, "A", "imm")
    op(base + 0x09, mn, "dp", "dps")
    op(base + 0x14, mn, "A", "dpx")
    op(base + 0x15, mn, "A", "absx")
    op(base + 0x16, mn, "A", "absy")
    op(base + 0x17, mn, "A", "idy")
    op(base + 0x18, mn, "dp", "imm")
    op(base + 0x19, mn, "ix", "iy")
for b in range(8):
    op(b << 5 | 0x02, "SET1", "dpbit")
    op(b << 5 | 0x12, "CLR1", "dpbit")
    op(b << 5 | 0x03, "BBS", "dpbit", "rel")
    op(b << 5 | 0x13, "BBC", "dpbit", "rel")
for n in range(16):
    op(n << 4 | 0x01, "TCALL", "tcall")
SH = {0x00: "ASL", 0x20: "ROL", 0x40: "LSR", 0x60: "ROR"}
for base, mn in SH.items():
    op(base + 0x0B, mn, "dp")
    op(base + 0x0C, mn, "abs")
    op(base + 0x1B, mn, "dpx")
    op(base + 0x1C, mn, "A")
op(0x8B, "DEC", "dp"); op(0x8C, "DEC", "abs"); op(0x9B, "DEC", "dpx"); op(0x9C, "DEC", "A")
op(0xAB, "INC", "dp"); op(0xAC, "INC", "abs"); op(0xBB, "INC", "dpx"); op(0xBC, "INC", "A")
op(0x1D, "DEC", "X"); op(0xDC, "DEC", "Y"); op(0x3D, "INC", "X"); op(0xFC, "INC", "Y")
op(0x00, "NOP"); op(0x0F, "BRK"); op(0x6F, "RET"); op(0x7F, "RETI")
op(0xEF, "SLEEP"); op(0xFF, "STOP")
op(0x20, "CLRP"); op(0x40, "SETP"); op(0x60, "CLRC"); op(0x80, "SETC"); op(0xA0, "EI")
op(0xC0, "DI"); op(0xE0, "CLRV"); op(0xED, "NOTC")
op(0x0D, "PUSH", "PSW"); op(0x2D, "PUSH", "A"); op(0x4D, "PUSH", "X"); op(0x6D, "PUSH", "Y")
op(0x8E, "POP", "PSW"); op(0xAE, "POP", "A"); op(0xCE, "POP", "X"); op(0xEE, "POP", "Y")
op(0x0A, "OR1", "C", "membit"); op(0x2A, "OR1", "C", "nmembit")
op(0x4A, "AND1", "C", "membit"); op(0x6A, "AND1", "C", "nmembit")
op(0x8A, "EOR1", "C", "membit"); op(0xAA, "MOV1", "C", "membit")
op(0xCA, "MOV1", "membit", "C"); op(0xEA, "NOT1", "membit")
op(0x0E, "TSET1", "abs"); op(0x4E, "TCLR1", "abs")
op(0x10, "BPL", "rel"); op(0x30, "BMI", "rel"); op(0x50, "BVC", "rel"); op(0x70, "BVS", "rel")
op(0x90, "BCC", "rel"); op(0xB0, "BCS", "rel"); op(0xD0, "BNE", "rel"); op(0xF0, "BEQ", "rel")
op(0x2F, "BRA", "rel")
op(0x1A, "DECW", "dp"); op(0x3A, "INCW", "dp"); op(0x5A, "CMPW", "YA", "dp")
op(0x7A, "ADDW", "YA", "dp"); op(0x9A, "SUBW", "YA", "dp"); op(0xBA, "MOVW", "YA", "dp")
op(0xDA, "MOVW", "dp", "YA")
op(0x1E, "CMP", "X", "abs"); op(0x3E, "CMP", "X", "dp"); op(0x5E, "CMP", "Y", "abs")
op(0x7E, "CMP", "Y", "dp"); op(0xC8, "CMP", "X", "imm"); op(0xAD, "CMP", "Y", "imm")
op(0x1F, "JMP", "iabsx"); op(0x5F, "JMP", "abs"); op(0x3F, "CALL", "abs"); op(0x4F, "PCALL", "upage")
op(0x2E, "CBNE", "dp", "rel"); op(0xDE, "CBNE", "dpx", "rel")
op(0x6E, "DBNZ", "dp", "rel"); op(0xFE, "DBNZ", "Y", "rel")
op(0x5D, "MOV", "X", "A"); op(0x7D, "MOV", "A", "X"); op(0x9D, "MOV", "X", "SP")
op(0xBD, "MOV", "SP", "X"); op(0xDD, "MOV", "A", "Y"); op(0xFD, "MOV", "Y", "A")
op(0x8D, "MOV", "Y", "imm"); op(0xCD, "MOV", "X", "imm"); op(0x8F, "MOV", "dp", "imm")
op(0xFA, "MOV", "dp", "dps")
op(0xAF, "MOV", "ixinc", "A"); op(0xBF, "MOV", "A", "ixinc")
op(0xC4, "MOV", "dp", "A"); op(0xC5, "MOV", "abs", "A"); op(0xC6, "MOV", "ix", "A")
op(0xC7, "MOV", "idx", "A"); op(0xD4, "MOV", "dpx", "A"); op(0xD5, "MOV", "absx", "A")
op(0xD6, "MOV", "absy", "A"); op(0xD7, "MOV", "idy", "A")
op(0xC9, "MOV", "abs", "X"); op(0xCB, "MOV", "dp", "Y"); op(0xCC, "MOV", "abs", "Y")
op(0xD8, "MOV", "dp", "X"); op(0xD9, "MOV", "dpy", "X"); op(0xDB, "MOV", "dpx", "Y")
op(0xE4, "MOV", "A", "dp"); op(0xE5, "MOV", "A", "abs"); op(0xE6, "MOV", "A", "ix")
op(0xE7, "MOV", "A", "idx"); op(0xE8, "MOV", "A", "imm"); op(0xF4, "MOV", "A", "dpx")
op(0xF5, "MOV", "A", "absx"); op(0xF6, "MOV", "A", "absy"); op(0xF7, "MOV", "A", "idy")
op(0xE9, "MOV", "X", "abs"); op(0xEB, "MOV", "Y", "dp"); op(0xEC, "MOV", "Y", "abs")
op(0xF8, "MOV", "X", "dp"); op(0xF9, "MOV", "X", "dpy"); op(0xFB, "MOV", "Y", "dpx")
op(0xCF, "MUL", "YA"); op(0x9E, "DIV", "YA", "X"); op(0x9F, "XCN", "A")
op(0xBE, "DAS", "A"); op(0xDF, "DAA", "A")
assert sorted(T) == list(range(256)), [hex(x) for x in range(256) if x not in T]

# ---------------------------------------------------------------------------------------------
# Encoding: the operand bytes after the opcode, in byte order, as SLEIGH pattern pieces.
# ---------------------------------------------------------------------------------------------
REG = {"A", "X", "Y", "YA", "SP", "PSW", "C"}


def pattern(code, modes):
    mm = [m for m in modes if m not in REG]
    if "dps" in mm:                                   # op src dst
        return ["SDP", "ADDR8"]
    if mm == ["dp", "imm"]:                           # op imm dst
        return ["imm8", "ADDR8"]
    seq = []
    for m in mm:
        seq.append({"imm": "imm8", "dp": "ADDR8", "dpx": "ADDR8", "dpy": "ADDR8", "idx": "ADDR8",
                    "idy": "ADDR8", "abs": "ADDR16", "absx": "ADDR16", "absy": "ADDR16",
                    "iabsx": "ADDR16", "rel": "RADDR8", "membit": "MEMBIT & membitno",
                    "nmembit": "MEMBIT & membitno",
                    "dpbit": "ADDR8", "upage": "UPAGE", "tcall": None, "ix": None, "iy": None,
                    "ixinc": None}[m])
    seq = [s for s in seq if s]
    if code in (0x3F, 0x5F):                          # CALL/JMP !abs: direct flow
        seq = ["ADDR16J"]
    return seq


# ---------------------------------------------------------------------------------------------
# Display: native (Sony) syntax.
# ---------------------------------------------------------------------------------------------
def native_operand(m, code):
    return {
        "A": '"A"', "X": '"X"', "Y": '"Y"', "YA": '"YA"', "SP": '"SP"', "PSW": '"PSW"',
        "C": '"C"',
        "imm": '"#"^imm8', "dp": "ADDR8", "dps": "SDP", "dpx": "ADDR8^\"+X\"",
        "dpy": "ADDR8^\"+Y\"", "abs": '"!"^ADDR16', "absx": '"!"^ADDR16^"+X"',
        "absy": '"!"^ADDR16^"+Y"', "idx": '"["^ADDR8^"+X]"', "idy": '"["^ADDR8^"]+Y"',
        "ix": '"(X)"', "iy": '"(Y)"', "ixinc": '"(X)+"', "rel": "RADDR8", "membit": "MEMBIT",
        "nmembit": '"/"^MEMBIT', "dpbit": 'ADDR8^"."^bitno', "tcall": "tcalln",
        "upage": "UPAGE", "iabsx": '"[!"^ADDR16^"+X]"',
    }[m]


def native_display(code):
    mn, modes = T[code]
    if not modes:
        return mn
    d = mn + " " + ",".join(native_operand(m, code) for m in modes)
    return d.replace("ADDR16", "ADDR16J") if code in (0x3F, 0x5F) else d


# ---------------------------------------------------------------------------------------------
# Display: 65816-style syntax from spc700.arch.
# ---------------------------------------------------------------------------------------------
ARCH = {}
for line in open(os.path.join(OUT, "spc700.arch")):
    line = line.rstrip()
    if not line or line.startswith("//") or line.startswith("endian") or ";" not in line:
        continue
    tmpl, enc = [x.strip() for x in line.split(";", 1)]
    if re.match(r"^\w+\.[wb] ", tmpl):
        continue                                       # explicit-size aliases
    m = re.match(r"\$([0-9a-f]{2})", enc)
    if m:
        ARCH[int(m.group(1), 16)] = tmpl
    elif enc.startswith("=a %0001"):
        for n in range(16):
            ARCH[n << 4 | 1] = tmpl
    else:
        bits = re.search(r"%([01]{5})", enc).group(1)
        for b in range(8):
            ARCH[b << 5 | int(bits, 2)] = tmpl
assert sorted(ARCH) == list(range(256)), [hex(x) for x in range(256) if x not in ARCH]


def arch_display(code):
    mn, modes = T[code]
    tmpl = ARCH[code]
    word, _, rest = tmpl.partition(" ")
    out = word.upper()
    if not rest:
        return out
    # map each *NN placeholder to an operand symbol, in template order
    mm = [m for m in modes if m not in REG]
    syms = []
    for m in mm:
        syms += {"imm": ["imm8"], "dp": ["ADDR8"], "dps": ["SDP"], "dpx": ["ADDR8"],
                 "dpy": ["ADDR8"], "abs": ["ADDR16"], "absx": ["ADDR16"], "absy": ["ADDR16"],
                 "idx": ["ADDR8"], "idy": ["ADDR8"], "rel": ["RADDR8"], "membit": ["MEMBIT"],
                 "nmembit": ["MEMBIT"], "dpbit": ["ADDR8", "bitno"], "tcall": ["tcalln"],
                 "upage": ["UPAGE"], "iabsx": ["ADDR16"], "ix": [], "iy": [], "ixinc": []}[m]
    # "dp,dp" and "dp,#imm": the template is "dst=src", Sony order is also (dst, src)
    parts = re.split(r"(\*\d\d(?::\*03)?)", rest)
    res = []
    k = 0
    for p in parts:
        if p.startswith("*"):
            if p == "*13:*03" or not p.endswith(":*03"):
                res.append(syms[k])
                k += 1
            else:                                      # dp:bit
                res += [syms[k], '":"', syms[k + 1]]
                k += 2
        elif p:
            res.append('"%s"' % p.upper().replace('"', ''))
    assert k == len(syms), (hex(code), tmpl, syms)
    d = out + " " + "^".join(res)
    return d.replace("ADDR16", "ADDR16J") if code in (0x3F, 0x5F) else d


# ---------------------------------------------------------------------------------------------
# Semantics.
# ---------------------------------------------------------------------------------------------
def ea(m, n="ea"):
    """p-code computing local <n>:2 for a memory operand mode (or None)."""
    e = {
        "dp": "local ea:2 = ADDR8;",
        "dps": "local ea:2 = SDP;",
        "dpx": "local ea:2 = (ADDR8 & 0xff00) | ((ADDR8 + zext(X)) & 0xff);",
        "dpy": "local ea:2 = (ADDR8 & 0xff00) | ((ADDR8 + zext(Y)) & 0xff);",
        "abs": "local ea:2 = ADDR16;",
        "absx": "local ea:2 = ADDR16 + zext(X);",
        "absy": "local ea:2 = ADDR16 + zext(Y);",
        "idx": "local ptr:2 = (ADDR8 & 0xff00) | ((ADDR8 + zext(X)) & 0xff); local ea:2; readdpw(ea, ptr);",
        "idy": "local ptr:2; readdpw(ptr, ADDR8); local ea:2 = ptr + zext(Y);",
        "ix": "local ea:2 = DPB | zext(X);",
        "iy": "local ea:2 = DPB | zext(Y);",
        "ixinc": "local ea:2 = DPB | zext(X);",
        "dpbit": "local ea:2 = ADDR8;",
    }.get(m)
    if e is None:
        return None
    return re.sub(r"\bea\b", n, re.sub(r"\bptr\b", n + "ptr", e))


def src_value(m, name="val"):
    if m in REG:
        return "local %s:1 = %s;" % (name, m)
    if m == "imm":
        return "local %s:1 = imm8;" % name
    return ea(m, "sea") + " local %s:1 = *:1 sea;" % name


def body(code):
    mn, modes = T[code]
    L = []
    if mn in ("OR", "AND", "EOR", "ADC", "SBC", "CMP") and modes[0] in ("A", "dp", "ix") \
            and len(modes) == 2 and modes != ["X", "abs"]:
        dst, src = modes
        L.append(src_value(src, "val"))
        if dst == "A":
            L.append("local cur:1 = A;")
        else:
            L.append(ea(dst))
            L.append("local cur:1 = *:1 ea;")
        if mn == "CMP":
            L.append("compare(cur, val);")
            return L
        L.append("local res:1;")
        L.append({"OR": "res = cur | val; nz(res);", "AND": "res = cur & val; nz(res);",
                  "EOR": "res = cur ^ val; nz(res);", "ADC": "adc(res, cur, val);",
                  "SBC": "sbc(res, cur, val);"}[mn])
        L.append("A = res;" if dst == "A" else "*:1 ea = res;")
        return L
    if mn == "CMP":                                    # CMP X/Y,...
        dst, src = modes
        L.append(src_value(src, "val"))
        L.append("compare(%s, val);" % dst)
        return L
    if mn == "MOV":
        dst, src = modes
        if dst in REG and src in REG:
            if dst == "SP":
                return ["SP = 0x100 | zext(X);"]
            if src == "SP":
                return ["X = SP:1;", "nz(X);"]
            return ["%s = %s;" % (dst, src), "nz(%s);" % dst]
        if dst in REG:                                 # load
            L.append(src_value(src, "val"))
            L.append("%s = val;" % dst)
            L.append("nz(%s);" % dst)
            if src == "ixinc":
                L.append("X = X + 1;")
            return L
        # store
        L.append(src_value(src, "val"))
        L.append(ea(dst))
        L.append("*:1 ea = val;")
        if dst == "ixinc":
            L.append("X = X + 1;")
        return L
    if mn in ("ASL", "ROL", "LSR", "ROR", "INC", "DEC"):
        m = modes[0]
        if m in REG:
            L.append("local v:1 = %s;" % m)
        else:
            L.append(ea(m))
            L.append("local v:1 = *:1 ea;")
        L.append({"ASL": "local c:1 = v >> 7; v = v << 1; CF = c;",
                  "ROL": "local c:1 = v >> 7; v = (v << 1) | CF; CF = c;",
                  "LSR": "local c:1 = v & 1; v = v >> 1; CF = c;",
                  "ROR": "local c:1 = v & 1; v = (v >> 1) | (CF << 7); CF = c;",
                  "INC": "v = v + 1;", "DEC": "v = v - 1;"}[mn])
        L.append("nz(v);")
        L.append("%s = v;" % m if m in REG else "*:1 ea = v;")
        return L
    if mn == "XCN":
        return ["A = (A >> 4) | (A << 4);", "nz(A);"]
    if mn in ("MOVW", "INCW", "DECW", "ADDW", "SUBW", "CMPW"):
        L.append("local w:2; readdpw(w, ADDR8);" if not (mn == "MOVW" and modes[0] == "dp") else "")
        L.append({"MOVW": "YA = w; nz16(YA);" if modes[0] == "YA" else "writedpw(ADDR8, YA);",
                  "INCW": "w = w + 1; nz16(w); writedpw(ADDR8, w);",
                  "DECW": "w = w - 1; nz16(w); writedpw(ADDR8, w);",
                  "ADDW": "addw(w);", "SUBW": "subw(w);",
                  "CMPW": "local r:2 = YA - w; CF = YA >= w; nz16(r);"}[mn])
        return [x for x in L if x]
    if mn == "MUL":
        return ["YA = zext(Y) * zext(A);", "nz(Y);"]
    if mn == "DIV":
        return ["divide();"]
    if mn == "DAA":
        return ["daa();"]
    if mn == "DAS":
        return ["das();"]
    cond = {"BPL": "NF == 0", "BMI": "NF == 1", "BVC": "VF == 0", "BVS": "VF == 1",
            "BCC": "CF == 0", "BCS": "CF == 1", "BNE": "ZF == 0", "BEQ": "ZF == 1"}
    if mn in cond:
        return ["if (%s) goto RADDR8;" % cond[mn]]
    if mn == "BRA":
        return ["goto RADDR8;"]
    if mn in ("BBS", "BBC"):
        return ["local v:1 = *:1 ADDR8;",
                "if (((v >> bitno) & 1) %s 0) goto RADDR8;" % ("!=" if mn == "BBS" else "==")]
    if mn in ("SET1", "CLR1"):
        return ["local v:1 = *:1 ADDR8;",
                "*:1 ADDR8 = v %s;" % ("| (1 << bitno)" if mn == "SET1" else "& ~(1 << bitno)")]
    if mn == "CBNE":
        return [ea(modes[0]), "local v:1 = *:1 ea;", "if (A != v) goto RADDR8;"]
    if mn == "DBNZ":
        if modes[0] == "Y":
            return ["Y = Y - 1;", "if (Y != 0) goto RADDR8;"]
        return ["local v:1 = *:1 ADDR8 - 1;", "*:1 ADDR8 = v;", "if (v != 0) goto RADDR8;"]
    if mn == "JMP":
        if modes[0] == "abs":
            return ["goto ADDR16J;"]
        return ["local ptr:2 = ADDR16 + zext(X);", "local t:2 = *:2 ptr;", "goto [t];"]
    if mn == "CALL":
        return ["local ret:2 = inst_next; push16(ret);", "call ADDR16J;"]
    if mn == "PCALL":
        return ["local ret:2 = inst_next; push16(ret);", "call UPAGE;"]
    if mn == "TCALL":
        return ["local ret:2 = inst_next; push16(ret);", "local vec:2 = 0xffde - 2 * tcalln;",
                "local t:2 = *:2 vec;", "call [t];"]
    if mn == "BRK":
        return ["local ret:2 = inst_next; push16(ret);", "local p:1; packpsw(p); push8(p);", "BF = 1;", "IF = 0;",
                "local t:2 = *:2 0xffde:2;", "call [t];"]
    if mn == "RET":
        return ["local t:2; pop16(t);", "return [t];"]
    if mn == "RETI":
        return ["local p:1; pop8(p); unpackpsw(p);", "local t:2; pop16(t);", "return [t];"]
    if mn == "PUSH":
        r = modes[0]
        if r == "PSW":
            return ["local p:1; packpsw(p);", "push8(p);"]
        return ["push8(%s);" % r]
    if mn == "POP":
        r = modes[0]
        if r == "PSW":
            return ["local p:1; pop8(p);", "unpackpsw(p);"]
        return ["pop8(%s);" % r]
    if mn in ("OR1", "AND1", "EOR1", "MOV1", "NOT1"):
        L = ["local v:1 = *:1 MEMBIT;", "local bit:1 = (v >> membitno) & 1;"]
        neg = modes[-1] == "nmembit"
        if neg:
            L.append("bit = bit ^ 1;")
        if mn == "NOT1":
            return ["local v:1 = *:1 MEMBIT;", "*:1 MEMBIT = v ^ (1 << membitno);"]
        if mn == "MOV1" and modes[0] == "membit":
            return ["local v:1 = *:1 MEMBIT;",
                    "*:1 MEMBIT = (v & ~(1 << membitno)) | (CF << membitno);"]
        L.append({"OR1": "CF = CF | bit;", "AND1": "CF = CF & bit;", "EOR1": "CF = CF ^ bit;",
                  "MOV1": "CF = bit;"}[mn])
        return L
    if mn in ("TSET1", "TCLR1"):
        return ["local v:1 = *:1 ADDR16;", "local r:1 = A - v;", "nz(r);",
                "*:1 ADDR16 = v %s;" % ("| A" if mn == "TSET1" else "& ~A")]
    simple = {"NOP": [], "CLRP": ["PF = 0;"], "SETP": ["PF = 1;"], "CLRC": ["CF = 0;"],
              "SETC": ["CF = 1;"], "EI": ["IF = 1;"], "DI": ["IF = 0;"],
              "CLRV": ["VF = 0;", "HF = 0;"], "NOTC": ["CF = CF ^ 1;"],
              # SLEEP and STOP halt the CPU (the SNES gives the SPC700 no interrupt to wake it):
              # a self-loop, so nothing falls through and an emulator stays on the instruction
              # instead of failing on an unimplemented pcodeop.
              "SLEEP": ["goto inst_start;"], "STOP": ["goto inst_start;"]}
    return simple[mn]


def actions(code):
    mn, modes = T[code]
    if mn == "SETP":
        return "[ ctx_P=1; globalset(inst_next, ctx_P); ]"
    if mn == "CLRP":
        return "[ ctx_P=0; globalset(inst_next, ctx_P); ]"
    if mn == "PUSH" and modes == ["PSW"]:
        return ("[ ctx_svOK=1; globalset(inst_next, ctx_svOK); "
                "ctx_svP=ctx_P; globalset(inst_next, ctx_svP); ]")
    return ""


def constructor(code, display):
    mn, modes = T[code]
    pat = "op=0x%02X" % code
    pieces = pattern(code, modes)
    extra = ""
    if "tcall" in modes:
        extra = " & tcalln"
    if "dpbit" in modes:
        extra = " & bitno"
    head = ":%s is %s%s & DPB" % (display, pat, extra)
    if pieces:
        head += "; " + "; ".join(pieces)
    act = actions(code)
    lines = [head + (" " + act if act else "") + " {"]
    for l in body(code):
        lines.append("\t" + l)
    lines.append("}")
    if mn == "POP" and modes == ["PSW"]:
        # after a PUSH PSW on this flow path the pulled P is known: restore the decode context
        lines.append(head.replace("& DPB", "& DPB & ctx_svOK=1") +
                     " [ ctx_P=ctx_svP; globalset(inst_next, ctx_P); "
                     "ctx_svOK=0; globalset(inst_next, ctx_svOK); ] {")
        for l in body(code):
            lines.append("\t" + l)
        lines.append("}")
    return "\n".join(lines)


HDR = """# Generated by tools/gen_spc700.py -- edit the generator, not this file.
# %s
@include "spc700.sinc"

"""

MEMBIT = """# Absolute bit operand: 13-bit address and 3-bit bit number in one 16-bit word.
MEMBIT: mb_addr^"%s"^membitno is mb_addr & membitno { export *[const]:2 mb_addr; }

"""


def main():
    for name, disp, desc, sep in (("spc700-native.slaspec", native_display, "Sony mnemonics", "."),
                                  ("spc700-65816.slaspec", arch_display,
                                   "65816-style mnemonics (spc700.arch)", ":")):
        with open(os.path.join(OUT, name), "w") as f:
            f.write(HDR % desc)
            f.write(MEMBIT % sep)
            for code in range(256):
                f.write("# %02X\n%s\n\n" % (code, constructor(code, disp(code))))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
