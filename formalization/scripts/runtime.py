"""Validate and materialize the supplemental lean-runtime@1 input.

The manifest is an integrity inventory, not an independent provenance signature.
The caller must trust the supplied compiler and prebuilt dependency artifacts.
"""
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import stat

from common import Failure, LEAN, LEAN_URL, MATHLIB, SOURCES, read_json, require, run


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def payload(root):
    """Reject links (including directory links), devices, sockets and FIFOs."""
    found = {}
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(base) / name
            mode = path.lstat().st_mode
            require(stat.S_ISDIR(mode) or stat.S_ISREG(mode),
                    f"runtime contains a link or special file: {path.relative_to(root)}")
            if stat.S_ISREG(mode):
                rel = path.relative_to(root).as_posix()
                if rel != "runtime-manifest.json":
                    found[rel] = path
    return found


def source_entries():
    return [{"name": "lean", "url": LEAN_URL, "rev": LEAN}] + [
        {"name": name, "url": url, "rev": rev} for name, (url, rev) in SOURCES.items()]


def validate(root):
    root = Path(root).absolute()
    require(root.is_dir() and not root.is_symlink(), f"missing runtime directory: {root}")
    mf = root / "runtime-manifest.json"
    require(mf.is_file() and not mf.is_symlink(), "missing regular runtime-manifest.json")
    data = read_json(mf)
    require(isinstance(data, dict), "runtime manifest must be an object")
    for key, value in {"schema": "lean-runtime@1", "lean": LEAN,
                       "mathlib": MATHLIB, "platform": "linux-x64"}.items():
        require(data.get(key) == value, f"runtime {key} mismatch (expected {value})")
    sources = data.get("sources")
    require(isinstance(sources, list) and all(isinstance(s, dict) for s in sources),
            "runtime sources must be an array of objects")
    require(len({s.get('name') for s in sources}) == len(sources), "duplicate runtime source")
    require(sorted(sources, key=lambda s: s.get("name", "")) ==
            sorted(source_entries(), key=lambda s: s["name"]), "runtime source URLs/revisions mismatch")
    rows = data.get("files")
    require(isinstance(rows, list) and rows, "runtime files must be nonempty")
    indexed = {}
    for row in rows:
        require(isinstance(row, dict), "runtime file entry must be an object")
        p = row.get("path")
        require(isinstance(p, str) and p and "\\" not in p and
                not PurePosixPath(p).is_absolute() and
                all(part not in ("", ".", "..") for part in p.split("/")),
                f"unsafe runtime path: {p!r}")
        require(p != "runtime-manifest.json" and p not in indexed, f"duplicate/excluded runtime path: {p}")
        require(type(row.get("bytes")) is int and row["bytes"] >= 0 and
                isinstance(row.get("sha256"), str) and re.fullmatch(r"[0-9a-f]{64}", row["sha256"]),
                f"invalid runtime inventory row: {p}")
        indexed[p] = row
    actual = payload(root)
    require(actual.keys() == indexed.keys(),
            "runtime inventory mismatch: missing=" + str(sorted(indexed.keys() - actual.keys())[:5]) +
            " unlisted=" + str(sorted(actual.keys() - indexed.keys())[:5]))
    for name in ("lean", "lake"):
        p = root / "toolchain/bin" / name
        require(p.is_file() and os.access(p, os.X_OK), f"runtime executable missing: toolchain/bin/{name}")
    require((root / "toolchain/lib/lean/Init.olean").is_file(), "missing toolchain Init.olean")
    require((root / "src/mathlib/lean-toolchain").read_text().strip() == "leanprover/lean4:" + LEAN,
            "Mathlib lean-toolchain mismatch")
    lock = read_json(root / "src/mathlib/lake-manifest.json")
    locked = {p["name"]: (p["url"], p["rev"]) for p in lock["packages"]}
    require(locked == {k: v for k, v in SOURCES.items() if k != "mathlib"},
            "Mathlib transitive lock mismatch")
    for name in SOURCES:
        source = root / "src" / name
        require(source.is_dir() and any(source.glob("lakefile.*")), f"missing source package: {name}")
        cache = source / ".lake/build/lib/lean"
        require(cache.is_dir() and any(cache.rglob("*.olean")), f"missing prebuilt cache: {name}")
    print(f"runtime inventory: hashing {len(actual)} files", flush=True)
    for rel, path in sorted(actual.items()):
        row = indexed[rel]
        require(path.stat().st_size == row["bytes"] and digest(path) == row["sha256"],
                f"runtime checksum/size mismatch: {rel}")
    print(f"runtime inventory: OK ({len(actual)} files; {sum(r['bytes'] for r in rows)} bytes)", flush=True)
    return data


def write_manifest(root):
    root = Path(root)
    data = {"schema": "lean-runtime@1", "lean": LEAN, "mathlib": MATHLIB,
            "platform": "linux-x64", "sources": source_entries(),
            "files": [{"path": rel, "sha256": digest(path), "bytes": path.stat().st_size}
                      for rel, path in sorted(payload(root).items())]}
    import json
    (root / "runtime-manifest.json").write_text(json.dumps(data, indent=2) + "\n")


def materialize(root, destination):
    require(not destination.exists(), f"vendor destination already exists: {destination}")
    # cp reflinks are independent copies, never hard links back to the supplied runtime.
    run(["cp", "-a", "--reflink=auto", str(root), str(destination)], cwd=destination.parent)
    # Revalidate before touching permissions or executing any copied binary. This
    # also catches input changes during the copy, including newly introduced links.
    validate(destination)
    # Only directories need owner-write for eventual cleanup; cached files remain
    # read-only when supplied that way. Nothing is written to a dependency cache.
    for base, dirs, files in os.walk(destination):
        os.chmod(base, Path(base).stat().st_mode | stat.S_IWUSR | stat.S_IXUSR)
