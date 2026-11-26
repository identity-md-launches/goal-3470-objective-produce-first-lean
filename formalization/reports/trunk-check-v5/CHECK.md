# trunk-check-v5: independent rebuild and review of the RouteB wave

- Commit checked: `5fff4405e5b89976ab98ba3ca43215b47368b4e2` ("identitymd: wave 4 of goal 4b73084b…"). The public clone of
  `https://github.com/identity-md-launches/goal-3470-objective-produce-first-lean.git` has this commit, so the clean
  clone was taken at it.
- Toolchain: Lean 4.36.0 (commit 611c117b) from the `pequalnp-e125f04d0dc6` bundle, prebuilt packages bundle
  (Mathlib `fc4f59e577feb1a4956671bc04ac18aaaf8cd842` per the brief). Both archive sha256 values match `fetch.json`.
  The Mathlib revision inside the package bundle was not checked independently: UNVERIFIED.
- Compile command (per file, in an empty folder):
  `export PATH="$(ls -d D/lean/*/bin | head -n1):$PATH" LEAN_PATH="$(ls -d D/pk/*/.lake/build/lib/lean | paste -sd: -)" && lean -DautoImplicit=false X.lean`
- Raw output: [`check.log`](check.log).

## Result: all four expected files are ABSENT

The only `.lean` file at this commit (clean clone and checkout alike) is `formalization/MissingTheorems.lean`
(sha256 `582b25b3…`, a root module with no proof content). `git log --all` over the four expected paths is empty: they
were never committed on any branch of the public repository. `formalization/MissingTheorems/Target0{2,5,6,7}/RouteB/`
contain only the infrastructure `README.md`; `formalization/reports/Target0{2,5,6,7}/RouteB/REPORT.md` do not exist;
`formalization/manifest/declarations.json` has an empty `declarations` list.

| # | Path | Present | Expected sha256 | sha256 match | Exit code | Axioms | Verdict |
|---|------|---------|-----------------|--------------|-----------|--------|---------|
| 1 | `formalization/MissingTheorems/Target06/RouteB/CasoratiWeierstrass.lean` (`Complex.casorati_weierstrass`, Q2226962) | no | `32f7dc3209cc721457470f4746500f4c8f997550f4cfe8ee0665f2fe325c2154` | n/a (absent) | not run | not run | **FAIL** (absent) |
| 2 | `formalization/MissingTheorems/Target05/RouteB/Pompeiu.lean` (`EuclideanGeometry.pompeiu`, Q3534036) | no | `8b4912e3dfbe84664275a39e0a84d5a10bb3920cbf68af3231e11352610c364a` | n/a (absent) | not run | not run | **FAIL** (absent) |
| 3 | `formalization/MissingTheorems/Target07/RouteB/Midy.lean` (`Nat.midy`, Q856158) | no | `919c77a7eeab3c615464741eb08694461f2a90d8fa037cdfaf0bd6b9d971c6bf` | n/a (absent) | not run | not run | **FAIL** (absent) |
| 4 | `formalization/MissingTheorems/Target02/RouteB/InfiniteMonkey.lean` (`ProbabilityTheory.infinite_monkey`, Q487132) | no | `32a3a686681be51647b115fdca9f116b22eaf0a126ed3bf3085a045fccb979f7` | n/a (absent) | not run | not run | **FAIL** (absent) |

### Per-file detail

For each of the four: no source, so no forbidden-token search (`sorry`, `admit`, `native_decide`, `axiom`, `unsafe`,
`implemented_by`, `extern`, `opaque`), no compilation, no `#print axioms`, and no fidelity review (statement vs docstring
vs REPORT.md) was possible. Everything about these theorems (that they compile, their axioms, their faithfulness, the
prior-work check) stays UNVERIFIED. If they land later, the expected sha256 values above are the ones to compare against.

### Toolchain smoke test

To show the compile command and the bundle work, a scratch file importing Mathlib was compiled (exit 0, ~6 s);
`#print axioms Complex.exp_add` printed `[propext, Classical.choice, Quot.sound]`. This is not a deliverable and
proves nothing about the missing files.

## What stays UNVERIFIED

- All four theorems (absent).
- The Mathlib revision inside the package bundle (taken from the brief).
- `lake build` of the project: it needs the runtime `formalization/scripts/prepare_runtime.*` prepares; it was not run.
