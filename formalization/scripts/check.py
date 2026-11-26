#!/usr/bin/env python3
"""Proof scan, manifest validation, direct project build, and strict axiom parsing.

Token scanning is a conservative screen, NOT a complete kernel audit.
The executable CLI is harness.py (or the shell entry points).
"""
from pathlib import Path
import json
import re
import tomllib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import Failure, SOURCES, read_json, require, run

ALLOWED = {"propext", "Classical.choice", "Quot.sound"}
BANNED = re.compile(r"(?<![\w'])(sorry|admit|native_decide|axiom|sorryAx|implemented_by|extern|"
                    r"unsafe|ofReduceBool|ofReduceNat|trustCompiler|opaque|noncomputable_axiom)(?![\w'])")


def strip(src):
    """Blank comments and strings, preserving every offset/newline and token boundary."""
    out = list(src)
    i, n, depth = 0, len(src), 0
    while i < n:
        start = i
        if src.startswith("/-", i):
            depth = 1
            i += 2
            while i < n and depth:
                if src.startswith("/-", i):
                    depth += 1
                    i += 2
                elif src.startswith("-/", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            require(depth == 0, "unterminated block comment")
        elif src.startswith("--", i):
            i = src.find("\n", i)
            if i == -1:
                i = n
        elif src[i] == '"':
            i += 1
            while i < n and src[i] != '"':
                i += 2 if src[i] == "\\" else 1
            require(i < n, "unterminated string")
            i += 1
        else:
            i += 1
            continue
        for j in range(start, min(i, n)):
            if out[j] != "\n":
                out[j] = " "
    return "".join(out)


def project_files(root):
    return sorted([p for p in root.glob("*.lean") if p.name != "lakefile.lean"] +
                  list((root / "MissingTheorems").rglob("*.lean")))


def scan(root):
    files, hits = project_files(root), []
    require(root / "MissingTheorems.lean" in files, "missing root MissingTheorems.lean")
    for path in files:
        require(not path.is_symlink(), f"project source symlink: {path}")
        src = strip(path.read_text(encoding="utf-8"))
        for match in BANNED.finditer(src):
            line = src.count("\n", 0, match.start()) + 1
            hits.append(f"{path.relative_to(root)}:{line}: {match.group()}")
    for hit in hits:
        print("BANNED " + hit, flush=True)
    require(not hits, f"forbidden proof escapes: {len(hits)} hit(s)")
    print(f"token scan: OK ({len(files)} modules, including root); NOT a complete kernel audit", flush=True)


def identifier(value):
    if not isinstance(value, str) or not value:
        return False
    return all(part and (part[0].isalpha() or part[0] == "_") and
               all(c.isalnum() or c in "_'" for c in part) for part in value.split("."))


def module_file(root, module):
    require(identifier(module) and (module == "MissingTheorems" or module.startswith("MissingTheorems.")),
            f"invalid project module: {module!r}")
    path = root.joinpath(*module.split(".")).with_suffix(".lean")
    require(path.is_file() and not path.is_symlink(), f"missing module file: {module}")
    return path


def manifests(root, selected=None, module=None, infrastructure_only=False):
    if selected:
        paths = [Path(selected)]
    else:
        paths = sorted((root / "reports").glob("Target[0-9][0-9]/Route[AB]/declarations.json"))
        legacy = root / "manifest/declarations.json"
        # The original empty infrastructure registry is not a proof claim. Route registries
        # can coexist with it without editing this shared file.
        if legacy.exists():
            obj = read_json(legacy)
            require(isinstance(obj, dict) and isinstance(obj.get("declarations"), list),
                    f"invalid declaration manifest: {legacy}")
            if obj["declarations"] or not paths:
                paths.insert(0, legacy)
    require(paths or infrastructure_only, "no declaration manifests found")
    records, seen = [], set()
    for path in paths:
        require(path.is_file() and not path.is_symlink(), f"missing manifest file: {path}")
        obj = read_json(path)
        require(isinstance(obj, dict) and isinstance(obj.get("declarations"), list),
                f"invalid declaration manifest: {path}")
        rows = obj["declarations"]
        require(rows or infrastructure_only, f"empty declaration manifest: {path}")
        route = re.search(r"(?:^|/)reports/(Target\d\d)/(Route[AB])/declarations\.json$", path.as_posix())
        for row in rows:
            require(isinstance(row, dict), f"invalid declaration entry: {path}")
            name, mod = row.get("name"), row.get("module")
            require(identifier(name), f"invalid/missing declaration name: {name!r}")
            module_file(root, mod)
            require(name not in seen, f"duplicate declaration: {name}")
            require(not module or mod == module, f"manifest module {mod} does not match --module {module}")
            if route:
                target, branch = route.groups()
                prefix = f"MissingTheorems.{target}.{branch}."
                require(mod.startswith(prefix), f"route/module mismatch: {path}: {mod}")
                for key, expected in (("target", target), ("route", branch)):
                    require(key not in row or row[key] == expected, f"manifest {key} mismatch: {name}")
            seen.add(name)
            records.append({"name": name, "module": mod})
        print(f"manifest {path}: {len(rows)} declaration(s)", flush=True)
    require(records or infrastructure_only, "no proof declarations; use --infrastructure-only for an explicit empty check")
    if not records:
        print("UNVERIFIED proof gate: infrastructure-only empty mode", flush=True)
    return records


def build(root, env, module=None):
    """Lean itself parses the import graph; compile only project source modules.

    No Lake build scheduler is used: missing dependency oleans cannot trigger a build.
    Project options are read from the unchanged lakefile.toml.
    """
    lean = root / "vendor/toolchain/bin/lean"
    cache = root / ".lake/build/lib/lean"
    cache.mkdir(parents=True, exist_ok=True)
    env = dict(env)
    env["LEAN_PATH"] = ":".join([str(cache)] + [str(root / "vendor/src" / n / ".lake/build/lib/lean") for n in SOURCES])
    env["LEAN_SRC_PATH"] = ":".join([str(root)] + [str(root / "vendor/src" / n) for n in SOURCES])
    opts = tomllib.loads((root / "lakefile.toml").read_text())["leanOptions"]
    def option_pairs(table, prefix=""):
        for name, value in table.items():
            key = prefix + name
            if isinstance(value, dict):
                yield from option_pairs(value, key + ".")
            else:
                require(isinstance(value, (str, bool, int)), f"unsupported Lean option: {key}")
                yield key, value
    flags = ["-D" + name + "=" + (str(value).lower() if isinstance(value, bool) else str(value))
             for name, value in option_pairs(opts)]
    files = project_files(root) if not module else [module_file(root, module)]
    project = {p.resolve() for p in project_files(root)}
    ordered, visiting, visited = [], set(), set()

    def visit(path):
        path = path.resolve()
        if path in visited:
            return
        require(path not in visiting, f"cyclic project imports: {path}")
        visiting.add(path)
        deps = run([lean, "--src-deps", path.relative_to(root)], cwd=root, env=env, capture=True)
        for dep in deps.splitlines():
            d = Path(dep).resolve()
            if d in project:
                visit(d)
            else:
                # Only the supplied toolchain/dependencies are permissible import sources.
                require(d.is_relative_to(root / "vendor/toolchain/src/lean") or
                        any(d.is_relative_to(root / "vendor/src" / n) for n in SOURCES),
                        f"import source outside project/runtime: {dep}")
        visiting.remove(path)
        visited.add(path)
        ordered.append(path)

    for path in files:
        visit(path)
    # Lean resolves a module root via a directory even before its olean exists.
    # Create directories only, never placeholder/stale project oleans.
    for path in ordered:
        (cache / path.relative_to(root).parent).mkdir(parents=True, exist_ok=True)
    # Check all direct external cache paths before compiling any project module.
    project_oleans = {cache / p.relative_to(root).with_suffix(".olean") for p in project}
    for path in ordered:
        deps = run([lean, "--deps", path.relative_to(root)], cwd=root, env=env, capture=True)
        for dep in deps.splitlines():
            d = Path(dep).resolve()
            require(d in project_oleans or d.is_file(), f"missing prebuilt dependency: {dep}")
    for path in ordered:
        rel = path.relative_to(root)
        output = cache / rel.with_suffix(".olean")
        output.parent.mkdir(parents=True, exist_ok=True)
        run([lean, *flags, "-o", output, rel], cwd=root, env=env)
    print(f"project build: OK ({len(ordered)} modules; dependency compilation disabled)", flush=True)
    return env


AXIOM_LINE = re.compile(r"'([^\n]+)' (?:depends on axioms: \[([^\]]*)\]|does not depend on any axioms)")


def parse_axioms(output, records):
    """Consume the ENTIRE output, exactly once per name. Unknown output fails closed."""
    seen, rest = {}, output.strip()
    while rest:
        match = AXIOM_LINE.match(rest)
        require(match is not None, f"unrecognized axiom output: {rest[:180]!r}")
        name, body = match.groups()
        require(name not in seen, f"duplicate axiom output: {name}")
        axioms = [] if body is None or not body.strip() else [a.strip() for a in body.split(",")]
        require(all(identifier(a) for a in axioms), f"malformed axiom list: {body}")
        require(len(axioms) == len(set(axioms)), f"duplicate axiom in output: {name}")
        require(not set(axioms) - ALLOWED, f"forbidden axiom for {name}: {sorted(set(axioms) - ALLOWED)}")
        seen[name] = axioms
        rest = rest[match.end():].strip()
    require(set(seen) == {r["name"] for r in records}, "missing or unexpected declaration in axiom output")
    return seen


def axioms(root, env, records):
    if not records:
        print("axiom check: SKIPPED (explicit infrastructure-only empty mode)", flush=True)
        return
    lines = ["import Lean"] + ["import " + m for m in sorted({r["module"] for r in records})]
    for row in records:
        name, mod = row["name"], row["module"]
        # Check the defining module in Lean's environment, not just the name's prefix.
        lines += ["run_cmd do", "  let env ← Lean.getEnv",
                  f"  let decl := {json.dumps(name, ensure_ascii=False)}.toName",
                  "  unless env.contains decl do throwError \"missing declaration\"",
                  "  let some idx := env.getModuleIdxFor? decl | throwError \"missing defining module\"",
                  f'  unless env.header.moduleNames[idx.toNat]! == {json.dumps(mod, ensure_ascii=False)}.toName do',
                  f'    throwError "declaration/module mismatch: {name} expected {mod}"',
                  f"#print axioms {name}"]
    path = root / ".lake/axioms_check.lean"
    path.write_text("\n".join(lines) + "\n")
    output = run([root / "vendor/toolchain/bin/lean", path], cwd=root, env=env, capture=True)
    print(output, end="", flush=True)
    parse_axioms(output, records)
    print(f"axiom check: OK ({len(records)} declarations; allowed: {', '.join(sorted(ALLOWED))})", flush=True)


if __name__ == "__main__":
    import os
    os.execv(sys.executable, [sys.executable, "-I", str(Path(__file__).with_name("harness.py")), *sys.argv[1:]])
