#!/usr/bin/env python3
"""Explicit online preparation, split into bounded phases; never builds Mathlib modules."""
import argparse
import concurrent.futures
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Failure, LEAN_SHA, LEAN_URL, ROOT, SOURCES, clean_env, require, run
from runtime import digest, validate, write_manifest


def online_env(work, toolchain=None):
    env = clean_env(work, toolchain)
    # Only online transport settings are forwarded. Never log their values.
    for key in ("http_proxy", "https_proxy", "all_proxy", "no_proxy",
                "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def download(url, destination, work):
    run(["curl", "-q", "--fail", "--location", "--silent", "--show-error",
         "--max-time", "450", "--output", destination, url], cwd=work, env=online_env(work), timeout=460)


def normalize_links(root):
    for path in list(root.rglob("*")):
        if path.is_symlink():
            target = path.resolve(strict=True)
            require(target.is_relative_to(root.resolve()) and target.is_file(),
                    f"source/toolchain symlink escapes payload or names a directory: {path}")
            path.unlink()
            shutil.copy2(target, path)


def sources(root, scratch):
    require(not (root / "src").exists(), "src already exists; use a fresh runtime directory for sources phase")
    stage = scratch / "src"
    stage.mkdir()

    def get(item):
        name, (url, rev) = item
        archive = scratch / (name + ".tar.gz")
        download(url.replace("https://github.com/", "https://codeload.github.com/") + "/tar.gz/" + rev, archive, scratch)
        unpack = scratch / (name + "-unpack")
        unpack.mkdir()
        with tarfile.open(archive) as tar:
            tar.extractall(unpack, filter="data")
        top = list(unpack.iterdir())
        require(len(top) == 1 and top[0].is_dir(), f"unexpected archive layout: {name}")
        shutil.move(str(top[0]), stage / name)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(get, SOURCES.items()))
    normalize_links(stage)
    shutil.move(str(stage), root / "src")


def toolchain(root, scratch):
    require(not (root / "toolchain").exists(), "toolchain already exists; use a fresh runtime directory")
    archive = scratch / "lean.tar.zst"
    download(LEAN_URL, archive, scratch)
    require(digest(archive) == LEAN_SHA, "public Lean release archive SHA256 mismatch")
    stage = scratch / "toolchain"
    stage.mkdir()
    run(["tar", "--zstd", "-xf", archive, "--strip-components=1", "-C", stage], cwd=scratch)
    normalize_links(stage)
    shutil.move(str(stage), root / "toolchain")


def cache(root, scratch):
    require((root / "toolchain/bin/lake").is_file(), "run toolchain phase first")
    require(all((root / "src" / name).is_dir() for name in SOURCES), "run sources phase first")
    # Use an ephemeral copy of the unchanged package configuration to resolve the
    # exact path dependencies. Only Cache (and its small Batteries helper) and Cli
    # targets are compiled. There is no Mathlib-library build command here.
    project = scratch / "project"
    project.mkdir()
    for name in ("lakefile.toml", "lake-manifest.json", "lean-toolchain"):
        shutil.copyfile(ROOT / name, project / name)
    vendor = project / "vendor"
    vendor.mkdir()
    # Links exist only in online preparation scaffolding, never in the runtime.
    (vendor / "src").symlink_to(root / "src", target_is_directory=True)
    (vendor / "toolchain").symlink_to(root / "toolchain", target_is_directory=True)
    env = online_env(scratch, root / "toolchain")
    env["GIT_CEILING_DIRECTORIES"] = str(root)
    lake = root / "toolchain/bin/lake"
    run([lake, "build", "mathlib/cache:exe", "Cli"], cwd=project, env=env)
    mathlib = root / "src/mathlib"
    env["LEAN_SRC_PATH"] = ":".join(str(root / "src" / name) for name in SOURCES)
    # The same pinned executable as `lake exe cache get`, invoked directly so
    # Lake cannot update dependencies or schedule a Mathlib library build.
    run([mathlib / ".lake/build/bin/cache", "get", "--repo=leanprover-community/mathlib4"], cwd=mathlib, env=env)
    packages = mathlib / ".lake/packages"
    if packages.exists():
        for package in packages.iterdir():
            require(package.name in SOURCES and package.name != "mathlib" and not package.is_symlink(),
                    f"unexpected cache package: {package.name}")
            if (package / ".lake/build").exists():
                shutil.copytree(package / ".lake/build", root / "src" / package.name / ".lake/build", dirs_exist_ok=True)
        shutil.rmtree(packages)
    normalize_links(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online", action="store_true", required=True, help="explicitly authorize public downloads")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--phase", choices=("sources", "toolchain", "cache", "seal"), required=True)
    args = parser.parse_args()
    root = args.output.absolute()
    require(not root.is_symlink(), "runtime output cannot be a symlink")
    root.mkdir(parents=True, exist_ok=True)
    require(not (root / "runtime-manifest.json").exists(), "sealed runtime is immutable; prepare a new directory")
    with tempfile.TemporaryDirectory(prefix="lean-prepare-", dir=root.parent) as tmp:
        scratch = Path(tmp)
        if args.phase == "seal":
            write_manifest(root)
            try:
                validate(root)
            except Exception:
                (root / "runtime-manifest.json").unlink()
                raise
        else:
            globals()[args.phase](root, scratch)
    print(f"online preparation phase {args.phase}: PASS", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (Failure, OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print(f"FAIL: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)
