# MissingTheorems — Lean 4 infrastructure for the 1000+ theorems "missing" list

Infrastructure only: **no named theorem is proved here.** Pins: Lean `leanprover/lean4:v4.36.0`,
Mathlib `v4.36.0` = `fc4f59e577feb1a4956671bc04ac18aaaf8cd842` (2026-11-16). License Apache-2.0 (`LICENSE`;
vendored sources keep their own Apache-2.0 licenses, see `vendor/PROVENANCE.md`, `NOTICE`).

## Commands (run from the repository root; each is bounded to 540 s)
```
formalization/scripts/bootstrap.sh     # verify+extract vendored sources, install toolchain, install prebuilt Mathlib oleans
formalization/scripts/build.sh         # banned-token scan + lake build MissingTheorems (all present modules)
formalization/scripts/axioms.sh        # #print axioms for each entry of manifest/declarations.json
formalization/scripts/check_all.sh     # build.sh && axioms.sh
formalization/scripts/offline_test.sh  # fresh-copy, no-proxy test (needs vendor/payload/)
```
Never run `lake update` or build Mathlib from source: dependencies are `path` requires into `vendor/src/`
(no git, no network), so `lake build` uses the prebuilt oleans.

## Layout for proof workers (no configuration changes needed)
`MissingTheorems/TargetNN/RouteA|RouteB/**.lean`, NN = 01..08, namespaces `MissingTheorems.TargetNN.RouteX`.
`lean_lib MissingTheorems` uses globs `MissingTheorems` and `MissingTheorems.+`, so new files are picked up
automatically (verified with temporary smoke modules in Target01/RouteA and Target08/RouteB, since removed).
Register each exported theorem in `manifest/declarations.json` (`name`, `module`, `wikidata`, `target`, `route`).
Rules enforced by `scripts/check.py`: no `sorry`, `admit`, `native_decide`, `axiom`, `unsafe`, `implemented_by`,
`extern`, `opaque`, `ofReduceBool` (comments/strings ignored); `#print axioms` must show only
`propext`, `Classical.choice`, `Quot.sound`. Missing module/declaration = failure.
Reserved: `reports/` (proof evidence), `triage/` (research dataset). Catalogue data: `catalogue/`.
Submission format: `docs/SUBMISSION_FORMAT.md`. Logs: `logs/`.

## Status / blockers
* Verified here: bootstrap from network (cache get), build, axiom check, negative tests, fresh-copy run with
  `vendor/payload/` supplied and proxies pointed at a dead port.
* NOT verified: true network isolation (kernel forbids network namespaces: `unshare -rn` fails), and a run
  from the committed files alone with no network — the 607 MB toolchain and 2.0 GB prebuilt oleans are too big
  to commit, so offline use needs `vendor/payload/` (see `vendor/PROVENANCE.md`). **UNVERIFIED.**

## Size blocker (update)
The submission limit is 8 MiB, so `vendor/` holds only provenance (`vendor/PROVENANCE.md`, hashes, licence).
`scripts/bootstrap.sh` fetches sources, toolchain and prebuilt cache (needs network once). A truly offline check
from committed files alone is impossible within the limit: **UNVERIFIED**. The `logs/` were produced by the earlier
full-vendored layout (offline run with payload supplied succeeded; see logs/offline-check.log).
