#!/usr/bin/env python3
"""Project checks. Usage (from anywhere): scripts/check.py banned | axioms [--manifest FILE]
banned : fail if any MissingTheorems/**/*.lean uses sorry, admit, native_decide, axiom, or
         trusted-compiler escape hatches (comments and string literals are ignored).
axioms : for each declaration in the manifest, run `#print axioms` and fail on sorryAx, on any
         axiom other than propext/Classical.choice/Quot.sound, on a missing module/declaration,
         or on a Lean error. Requires the project to be built (scripts/build.sh)."""
import json, os, re, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED = {"propext", "Classical.choice", "Quot.sound"}
BANNED = re.compile(r"(?<![\w.'])(sorry|admit|native_decide|axiom|sorryAx|implemented_by|extern|"
                    r"unsafe|ofReduceBool|opaque|noncomputable_axiom)(?![\w'])")

def strip(src):
    out, i, n, depth = [], 0, len(src), 0
    while i < n:
        if src.startswith("/-", i):
            depth += 1; i += 2; continue
        if depth and src.startswith("-/", i):
            depth -= 1; i += 2; continue
        if depth: i += 1; out.append("\n" if src[i-1] == "\n" else ""); continue
        if src.startswith("--", i):
            while i < n and src[i] != "\n": i += 1
            continue
        if src[i] == '"':
            i += 1
            while i < n and src[i] != '"': i += 2 if src[i] == "\\" else 1
            i += 1; out.append('""'); continue
        out.append(src[i]); i += 1
    return "".join(out)

def lean_files():
    for d, _, fs in os.walk(os.path.join(ROOT, "MissingTheorems")):
        for f in fs:
            if f.endswith(".lean"): yield os.path.join(d, f)

def banned():
    bad = 0
    for p in sorted(lean_files()):
        for ln, line in enumerate(strip(open(p, encoding="utf-8").read()).split("\n"), 1):
            for m in BANNED.finditer(line):
                print(f"BANNED {os.path.relpath(p, ROOT)}:{ln}: {m.group(1)}"); bad += 1
    print(f"banned-token scan: {'FAIL' if bad else 'OK'} ({bad} hits)")
    return 1 if bad else 0

def axioms(manifest):
    decls = json.load(open(manifest))["declarations"]
    print(f"manifest {manifest}: {len(decls)} declaration(s)")
    if not decls: print("axiom check: OK (nothing to check)"); return 0
    mods = sorted({d["module"] for d in decls}); bad = 0
    for m in mods:
        if not os.path.exists(os.path.join(ROOT, *m.split(".")) + ".lean"):
            print(f"FAIL module file missing for {m}"); bad += 1
    if bad: return 1
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    tmp = os.path.join(ROOT, "build", "axioms_check.lean")
    with open(tmp, "w") as f:
        f.write("\n".join(f"import {m}" for m in mods) + "\n")
        for d in decls: f.write(f"#print axioms {d['name']}\n")
    r = subprocess.run(["lake", "env", "lean", tmp], cwd=ROOT, capture_output=True, text=True)
    print(r.stdout + r.stderr)
    seen = {}
    for m in re.finditer(r"'([^']+)' (?:depends on axioms: \[([^\]]*)\]|does not depend on any axioms)", r.stdout, re.S):
        seen[m.group(1)] = {a.strip() for a in (m.group(2) or "").replace("\n", " ").split(",") if a.strip()}
    if r.returncode != 0: print("FAIL lean exited", r.returncode); bad += 1
    for d in decls:
        ax = seen.get(d["name"])
        if ax is None: print(f"FAIL no axiom report for {d['name']}"); bad += 1
        elif ax - ALLOWED: print(f"FAIL {d['name']} uses {sorted(ax - ALLOWED)}"); bad += 1
        else: print(f"OK   {d['name']}: {sorted(ax)}")
    print(f"axiom check: {'FAIL' if bad else 'OK'}")
    return 1 if bad else 0

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["banned"]: sys.exit(banned())
    if a[:1] == ["axioms"]:
        mf = a[a.index("--manifest") + 1] if "--manifest" in a else os.path.join(ROOT, "manifest", "declarations.json")
        sys.exit(axioms(mf))
    print(__doc__); sys.exit(2)
