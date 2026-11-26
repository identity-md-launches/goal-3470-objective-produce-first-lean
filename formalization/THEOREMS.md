# Index of formalized theorems

Index of the Lean files in `formalization/MissingTheorems/` that passed an independent rebuild and review.
Last check: [`reports/trunk-check-v5/CHECK.md`](reports/trunk-check-v5/CHECK.md), commit
`5fff4405e5b89976ab98ba3ca43215b47368b4e2`, 2026-11-26.

## Passed

None yet. No file has passed an independent check at the commit above.

| Wikidata | Title | Declaration | Path | Pins | docs/1000.yaml entry | Report |
|----------|-------|-------------|------|------|----------------------|--------|
| (none) | | | | | | |

## Failed or absent

These four were expected from the RouteB wave and are **absent** at commit `5fff440` (never committed on any branch).
They are not formalized in this repository. Everything about them is UNVERIFIED.

| Wikidata | Title | Expected declaration | Expected path | Expected sha256 | Status |
|----------|-------|----------------------|---------------|-----------------|--------|
| Q2226962 | Weierstrass–Casorati theorem | `Complex.casorati_weierstrass` | `MissingTheorems/Target06/RouteB/CasoratiWeierstrass.lean` | `32f7dc32…2c154` | ABSENT |
| Q3534036 | Pompeiu's theorem | `EuclideanGeometry.pompeiu` | `MissingTheorems/Target05/RouteB/Pompeiu.lean` | `8b4912e3…c364a` | ABSENT |
| Q856158 | Midy's theorem | `Nat.midy` | `MissingTheorems/Target07/RouteB/Midy.lean` | `919c77a7…c6bf` | ABSENT |
| Q487132 | Infinite monkey theorem | `ProbabilityTheory.infinite_monkey` | `MissingTheorems/Target02/RouteB/InfiniteMonkey.lean` | `32a3a686…79f7` | ABSENT |

Full sha256 values are in the CHECK.md table.

## How to compile one file

Pins: Lean 4.36.0, Mathlib `fc4f59e577feb1a4956671bc04ac18aaaf8cd842` (prebuilt), from release
`https://github.com/Identity-md/lean-bundles/releases/download/pequalnp-e125f04d0dc6/`.

1. Download `lean-4.36.0-linux.tar.zst` and `pequalnp-e125f04d0dc6-packages-lean-4.36.0-linux-x64.tar.zst`; check
   their sha256 against `fetch.json` in the same release (`2b7ab1ed…a6eb` and `69b68c74…8a88`).
2. Unpack into `D/lean` and `D/pk` (`tar --zstd -xf …`). Do not build Mathlib.
3. Copy the file `X.lean` into an empty folder and run:

```sh
export PATH="$(ls -d D/lean/*/bin | head -n1):$PATH" \
       LEAN_PATH="$(ls -d D/pk/*/.lake/build/lib/lean | paste -sd: -)"
lean -DautoImplicit=false X.lean
```

Add `#print axioms <declaration>` at the end of the file to see the axioms. A pass needs exit 0, no `sorry`
warning, and only `propext`, `Classical.choice`, `Quot.sound`.

## Limit

`lake build` needs the runtime that `formalization/scripts/prepare_runtime.sh` prepares, which is not committed. A
build from the committed files alone is UNVERIFIED. The checks recorded here compile each file on its own with
`lean`, as above.
