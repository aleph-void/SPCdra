#!/usr/bin/env python3
"""Fetch SingleStepTests/spc700 (MIT, github.com/SingleStepTests/spc700) at a pinned commit:
the first N tests (of 1,000) of every opcode.

  fetch-singlestep.py <out.json> [N]
"""
import json
import sys
import urllib.request

COMMIT = "67d15f492b2740964abd4efd1229e0ec9c342228"
URL = "https://raw.githubusercontent.com/SingleStepTests/spc700/%s/v1/%02x.json"
out, n = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1000
tests = []
for op in range(256):
    with urllib.request.urlopen(URL % (COMMIT, op)) as r:
        data = json.load(r)
    tests += [{"name": t["name"], "initial": t["initial"], "final": t["final"]} for t in data[:n]]
    print("%02x" % op, len(tests), file=sys.stderr, flush=True)
json.dump(tests, open(out, "w"))
