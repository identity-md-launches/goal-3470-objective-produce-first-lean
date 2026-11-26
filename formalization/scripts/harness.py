#!/usr/bin/env python3
"""Bounded verification of fresh tracked project sources using a supplemental runtime."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

# -I omits the script directory; use only this known sibling directory for our modules.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Failure, LEAN, ROOT, clean_env, require, run
import check
from isolation import deny_network
import runtime


def snapshot(source, destination):
    repo = Path(run(["git", "rev-parse", "--show-toplevel"], cwd=source, capture=True).strip())
    relative = source.relative_to(repo)
    entries = run(["git", "-c", "core.fsmonitor=false", "ls-files", "--cached", "-z", "--", relative], cwd=repo, capture=True).split("\0")
    destination.mkdir()
    for entry in entries:
        if not entry:
            continue
        rel = Path(entry).relative_to(relative)
        if any(part in ("vendor", ".lake", "build", "logs", "__pycache__", ".git") for part in rel.parts):
            continue
        if rel.suffix in (".olean", ".ilean", ".o", ".so", ".a", ".trace", ".pyc"):
            continue
        src, dst = repo / entry, destination / rel
        require(src.is_file() and not src.is_symlink(), f"tracked file missing or symlink: {entry}")
        require(src.resolve().is_relative_to(source), f"tracked file escapes checkout: {entry}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    for name in ("lakefile.toml", "lake-manifest.json", "lean-toolchain", "MissingTheorems.lean"):
        require((destination / name).is_file(), f"missing tracked project file: {name}")
    require((destination / "lean-toolchain").read_text().strip() == "leanprover/lean4:" + LEAN,
            "project toolchain pin mismatch")
    # No edits to the package's dependency layout or its lock file are necessary.
    lock = __import__('json').loads((destination / "lake-manifest.json").read_text())
    require({p['name']: (p.get('type'), p.get('dir')) for p in lock['packages']} ==
            {name: ('path', f'vendor/src/{name}') for name in runtime.SOURCES}, "project path lock mismatch")
    print("snapshot: fresh tracked working-tree files; all project build artifacts excluded", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("banned", "validate-runtime", "bootstrap", "build", "axioms", "check", "offline"))
    parser.add_argument("--runtime", type=Path, help="read-only lean-runtime@1 directory (required except banned)")
    parser.add_argument("--module", help="build exactly this module and its project imports")
    parser.add_argument("--manifest", type=Path, help="one tracked manifest, relative to formalization/ or absolute")
    parser.add_argument("--infrastructure-only", action="store_true", help="explicitly allow an empty declaration set; no proof gate")
    parser.add_argument("--scratch-dir", type=Path, help="parent for disposable checkout (default: system temporary directory)")
    parser.add_argument("--keep-work", action="store_true", help="retain disposable checkout for inspection")
    args = parser.parse_args()
    if args.action == "banned":
        check.scan(ROOT)
        return
    require(args.runtime is not None, "--runtime DIR is required; no implicit downloads or vendor fallback")
    source_runtime = args.runtime.absolute()
    require((source_runtime / "runtime-manifest.json").is_file(), f"missing runtime manifest: {source_runtime}")
    if args.action == "validate-runtime":
        runtime.validate(source_runtime)
        return
    if args.manifest:
        selected = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
        require(selected.resolve().is_relative_to(ROOT), "--manifest must be inside formalization/")
        selected = selected.resolve().relative_to(ROOT)
    else:
        selected = None
    parent = args.scratch_dir.absolute() if args.scratch_dir else None
    if parent:
        parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="lean-harness-", dir=parent))
    try:
        project = work / "formalization"
        # Isolate even snapshot subprocesses, before any supplied tools execute.
        deny_network()
        snapshot(ROOT, project)
        check.scan(project)
        if args.module:
            check.module_file(project, args.module)
        records = []
        if args.action in ("axioms", "check", "offline"):
            records = check.manifests(project, project / selected if selected else None,
                                      args.module, args.infrastructure_only)
        runtime.validate(source_runtime)
        runtime.materialize(source_runtime, project / "vendor")
        toolchain = project / "vendor/toolchain"
        env = clean_env(project, toolchain)
        version = run([toolchain / "bin/lean", "--version"], cwd=project, env=env, capture=True)
        require("version 4.36.0," in version and "x86_64-unknown-linux-gnu" in version,
                "runtime Lean version/platform mismatch: " + version.strip())
        print(version, end="", flush=True)
        lake_version = run([toolchain / "bin/lake", "--version"], cwd=project, env=env, capture=True)
        require("4.36.0" in lake_version, "runtime Lake version mismatch: " + lake_version.strip())
        print(lake_version, end="", flush=True)
        if args.action != "bootstrap":
            env = check.build(project, env, args.module)
        if args.action in ("axioms", "check", "offline"):
            check.axioms(project, env, records)
        print(f"{args.action}: PASS (supplemental runtime; committed-only offline delivery is UNVERIFIED)", flush=True)
    finally:
        if args.keep_work:
            print(f"disposable checkout retained: {work}", flush=True)
        else:
            shutil.rmtree(work)


if __name__ == "__main__":
    try:
        main()
    except (Failure, OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print(f"FAIL: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)
