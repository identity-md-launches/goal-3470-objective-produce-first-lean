"""Shared constants and bounded, clean subprocess execution for the harness."""
import json
import os
from pathlib import Path
import shlex
import subprocess

LEAN = "v4.36.0"
MATHLIB = "fc4f59e577feb1a4956671bc04ac18aaaf8cd842"
LEAN_URL = "https://github.com/leanprover/lean4/releases/download/v4.36.0/lean-4.36.0-linux.tar.zst"
LEAN_SHA = "2b7ab1ed8b92d2e6abfaf41344823b510064dbc9c0260cac73eb496ab2dea6eb"
SOURCES = {
    "mathlib": ("https://github.com/leanprover-community/mathlib4", MATHLIB),
    "batteries": ("https://github.com/leanprover-community/batteries", "b4b25a3886a16daacaf6615c2eea7170a6e8f458"),
    "Qq": ("https://github.com/leanprover-community/quote4", "ff055a2fcc835935e0ae607339b455a5f5896b4b"),
    "aesop": ("https://github.com/leanprover-community/aesop", "66ff77cf0c4c898799e4b94d14db55f7a02d0c5a"),
    "proofwidgets": ("https://github.com/leanprover-community/ProofWidgets4", "2f0f3520daeac2d9310ff25b7a877a0e5cdaa203"),
    "importGraph": ("https://github.com/leanprover-community/import-graph", "8370c640afcd1cc3fb1cb9bf1560cc66eafee5e0"),
    "LeanSearchClient": ("https://github.com/leanprover-community/LeanSearchClient", "4fb58e749ef3fc0395fe274f6cab70c2ea85f1c9"),
    "plausible": ("https://github.com/leanprover-community/plausible", "054b228ce0ac61d767c6e71ba73a24728f191b72"),
    "Cli": ("https://github.com/leanprover/lean4-cli", "50810f72af7618bee62fe9800dc26e806c188703"),
}
ROOT = Path(__file__).resolve().parent.parent


class Failure(Exception):
    pass


def require(condition, message):
    if not condition:
        raise Failure(message)


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique)


def clean_env(work, toolchain=None):
    """An allowlist, not a copy of personal environment; HOME is never assigned."""
    work = Path(work).resolve()
    return {
        "PATH": (str(toolchain / "bin") + ":" if toolchain else "") + "/usr/bin:/bin",
        "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
        "ELAN_HOME": str(work / ".state/elan"),
        "XDG_CONFIG_HOME": str(work / ".state/config"),
        "CURL_HOME": str(work / ".state/curl"),
        "XDG_CACHE_HOME": str(work / ".state/cache"),
        "MATHLIB_CACHE_DIR": str(work / ".state/mathlib-cache"),
        "MATHLIB_NO_CACHE_ON_UPDATE": "1", "LAKE_NO_CACHE": "1",
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
    }


def run(command, *, cwd, env=None, capture=False, timeout=500):
    command = [str(x) for x in command]
    print("$ " + shlex.join(command), flush=True)
    result = subprocess.run(command, cwd=cwd, env=env or clean_env(cwd),
                            text=True, stdout=subprocess.PIPE if capture else None,
                            stderr=subprocess.STDOUT if capture else None, timeout=timeout)
    print(f"exit={result.returncode}", flush=True)
    if result.returncode:
        if capture:
            print(result.stdout, flush=True)
        raise Failure(f"command failed (exit {result.returncode}): {shlex.join(command)}")
    return result.stdout if capture else None
