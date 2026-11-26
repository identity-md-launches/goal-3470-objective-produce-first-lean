# MissingTheorems verification harness

This package is infrastructure only; it makes no named theorem claim. The package configuration and pins remain unchanged: Lean `leanprover/lean4:v4.36.0`, Mathlib `fc4f59e577feb1a4956671bc04ac18aaaf8cd842`. The current evidence is in `reports/infrastructure/`; older `build/` and `logs/` files describe earlier implementations.

## Offline verification

Supply a **separate, trusted runtime directory**. Committed files alone do not contain Lean or Mathlib caches and cannot perform an offline build. No script silently downloads a missing runtime.

From the repository root:

```sh
formalization/scripts/bootstrap.sh --runtime /path/to/runtime --scratch-dir test/scratch
formalization/scripts/build.sh --runtime /path/to/runtime --scratch-dir test/scratch
formalization/scripts/axioms.sh --runtime /path/to/runtime --scratch-dir test/scratch
formalization/scripts/check_all.sh --runtime /path/to/runtime --scratch-dir test/scratch
formalization/scripts/offline_test.sh --runtime /path/to/runtime --scratch-dir test/scratch
```

Every entry point is limited to 530 seconds, with a further 5-second termination grace period. It exits nonzero for missing inputs, bad checksums, compiler errors, failed axiom checks, inability to isolate networking, or timeout. There are no shell pipelines in the entry points. When capturing logs yourself, use redirection or `set -o pipefail` before a pipeline with `tee`.

All commands above validate the runtime and materialize independent copies into `vendor/toolchain` and `vendor/src` in a disposable checkout. `bootstrap.sh` tests that materialization and both tool versions; it does not install into the original checkout. `axioms.sh` builds its fresh sources before checking axioms, so it cannot reuse old project oleans. `--keep-work` retains the disposable checkout for inspection. Runtime input is never modified or hard-linked. File symlinks must be materialized by the runtime supplier; links, including internal links, and special files in a supplied runtime are rejected.

The snapshot contains **git-tracked files from the working tree**, including local edits to those files. Stage new proof files and manifests with `git add` before checking; a commit is unnecessary. Untracked files and all project `.lake`, `vendor`, `build`, and `logs` directories are excluded. Supplied dependency caches are retained. Scripts run from their current checkout, so harness changes can be tested before staging them.

Offline execution uses a clean environment allowlist, never assigns `HOME`, and never reads personal Git/Lake/Elan configuration. It installs an inherited Linux seccomp filter denying socket operations and io_uring, with IPv4, IPv6 and Unix socket probes. Linux x86-64, Python 3.11+ with `tarfile`'s `data` extraction filter, GNU coreutils, Git, and `libseccomp.so.2` are required. A host that cannot install this filter fails with an **UNVERIFIED network isolation** message. A dead proxy or failed HTTP request is never treated as isolation. This is network isolation for trusted build tools, not a general sandbox for hostile native code.

The offline builder asks Lean to parse each project's imports (`--src-deps`/`--deps`), sorts project modules by their dependencies, checks that external oleans exist, and invokes Lean directly with the options in the unchanged `lakefile.toml`. It does not invoke Lake's build scheduler, compile dependency modules, run `lake update`, or fetch a cache. Missing dependency artifacts are errors. Full builds discover the root and every `MissingTheorems/**/*.lean` module, even when the root imports none of them. Only the configured project's Lean modules are build targets; arbitrary Lake custom targets are outside this harness.

## Independent proof routes

Workers need not edit the root module or the shared declaration registry:

```sh
formalization/scripts/build.sh --runtime /path/to/runtime \
  --module MissingTheorems.Target01.RouteA.Result --scratch-dir test/scratch
formalization/scripts/axioms.sh --runtime /path/to/runtime \
  --module MissingTheorems.Target01.RouteA.Result \
  --manifest reports/Target01/RouteA/declarations.json --scratch-dir test/scratch
```

`--module` builds that module and its project imports. With `--manifest`, only the chosen manifest is checked; without it, full checks aggregate `reports/TargetNN/RouteA/declarations.json` and `RouteB/declarations.json` plus nonempty entries in `manifest/declarations.json`. The original empty shared registry is ignored when route manifests exist. A selected empty manifest, missing declaration, duplicate declaration across manifests, missing module, route/module mismatch, or declaration defined in another module fails. Names use ordinary dotted Lean identifiers (Unicode letters and primes supported; quoted identifiers are not supported).

A proof check requires at least one declaration. An infrastructure-only run on the empty package must say so explicitly:

```sh
formalization/scripts/offline_test.sh --runtime /path/to/runtime \
  --infrastructure-only --scratch-dir test/scratch
```

This reports the proof gate as **UNVERIFIED/SKIPPED**, even if infrastructure succeeds. It never supplies synthetic declarations to make an empty proof manifest pass.

The token scan covers `MissingTheorems.lean`, other root Lean modules, and every project submodule. It rejects `sorry`, `admit`, `native_decide`, new `axiom`s, `sorryAx`, `unsafe`, `implemented_by`, `extern`, `opaque`, and compiler reduction escape names; comments and strings are blanked without joining neighboring tokens. The axiom gate verifies each declaration's defining module in Lean's environment and executes genuine `#print axioms`. Only `propext`, `Classical.choice`, and `Quot.sound` are allowed. Missing, duplicate, or unrecognized output fails. **Token scanning is not a complete kernel audit**, and neither this harness nor an axiom list establishes that a statement faithfully expresses a named theorem. A separate fidelity and prior-work review is still required.

## Runtime input format

```text
runtime/
  toolchain/bin/lean
  toolchain/bin/lake
  toolchain/lib/lean/...       # matching public Lean release, including native libraries
  toolchain/src/lean/...
  src/mathlib/...             # pinned source and .lake/build caches
  src/batteries/...
  src/Qq/...
  src/aesop/...
  src/proofwidgets/...
  src/importGraph/...
  src/LeanSearchClient/...
  src/plausible/...
  src/Cli/...
  runtime-manifest.json
```

`runtime-manifest.json` uses this schema:

```json
{
  "schema": "lean-runtime@1",
  "lean": "v4.36.0",
  "mathlib": "fc4f59e577feb1a4956671bc04ac18aaaf8cd842",
  "platform": "linux-x64",
  "files": [{"path": "relative/payload/path", "sha256": "64 lowercase hexadecimal digits", "bytes": 123}],
  "sources": [{"name": "component", "url": "public pinned source URL", "rev": "pinned revision"}]
}
```

The file inventory must list **every regular payload file except the manifest**, exactly once. Paths are relative POSIX paths, without empty components, `.` or `..`. The example above describes the fields, not an installable runtime. Exact source entries, including the Lean release asset URL and each dependency's full revision, are defined in `scripts/common.py`; the preparation script writes them automatically. Lean's asset hash is checked during preparation. Verification checks the inventory, expected source metadata, Mathlib's own lock and toolchain file, cache presence for every dependency, executable version, and platform. The manifest is an integrity inventory, **not a signature proving provenance**; use a trusted supplier or prepare from the pinned public inputs below.

## Explicit online preparation

Preparation is a separate opt-in operation. Download and cache outputs belong outside submitted source, for example under `test/scratch`. Run each phase as its own bounded command:

```sh
formalization/scripts/prepare_runtime.sh --online --output test/scratch/runtime --phase sources
formalization/scripts/prepare_runtime.sh --online --output test/scratch/runtime --phase toolchain
formalization/scripts/prepare_runtime.sh --online --output test/scratch/runtime --phase cache
formalization/scripts/prepare_runtime.sh --online --output test/scratch/runtime --phase seal
```

Source archives use pinned public GitHub commits; the Lean public release is SHA256 checked. Only this online command forwards proxy transport variables. It suppresses personal curl/Git configuration. The cache phase builds the pinned Cache executable (and its small Batteries helper) and Cli, then runs that Cache executable's `get` command, equivalent to the download part of `lake exe cache get`. It never builds Mathlib library modules. Cache extraction's nested dependency artifacts are moved into the runtime's sibling dependency directories. No git submodules or permanent links are created. `seal` writes and verifies the complete manifest only after all inputs exist. An existing sealed runtime cannot be modified by preparation; choose a new output directory.

A partial or timed-out phase is not a runtime. Repair/retry that phase in scratch, or start a new output directory, before sealing. Each phase still has the 535-second outer bound. Supplemental runtime artifacts are intentionally not committed; **committed-only offline delivery remains UNVERIFIED/unavailable**. See `docs/SUBMISSION_FORMAT.md` for proof evidence and route manifest conventions.
