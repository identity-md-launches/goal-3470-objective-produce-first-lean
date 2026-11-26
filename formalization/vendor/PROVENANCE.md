# Provenance, versions, licenses (retrieved 2026-11-26)

| Component | Version / rev | Source | License | SHA256 of file in this repo |
|---|---|---|---|---|
| Lean 4 toolchain | v4.36.0 (commit 611c117bfaf7) | https://github.com/leanprover/lean4/releases/download/v4.36.0/lean-4.36.0-linux.tar.zst | Apache-2.0 (`vendor/LEAN-LICENSE`) | 2b7ab1ed8b92d2e6abfaf41344823b510064dbc9c0260cac73eb496ab2dea6eb (`vendor/payload/`, NOT committed: 607 MB) |
| Mathlib | v4.36.0 = fc4f59e577feb1a4956671bc04ac18aaaf8cd842 | https://github.com/leanprover-community/mathlib4/archive/<rev>.tar.gz | Apache-2.0 (`../LICENSE`) | see `sources/SHA256SUMS` |
| batteries | b4b25a3886a16daacaf6615c2eea7170a6e8f458 | leanprover-community/batteries | Apache-2.0 | `sources/SHA256SUMS` |
| Qq | ff055a2fcc835935e0ae607339b455a5f5896b4b | leanprover-community/quote4 | Apache-2.0 | `sources/SHA256SUMS` |
| aesop | 66ff77cf0c4c898799e4b94d14db55f7a02d0c5a | leanprover-community/aesop | Apache-2.0 | `sources/SHA256SUMS` |
| proofwidgets | 2f0f3520daeac2d9310ff25b7a877a0e5cdaa203 | leanprover-community/ProofWidgets4 | Apache-2.0 | `sources/SHA256SUMS` |
| importGraph | 8370c640afcd1cc3fb1cb9bf1560cc66eafee5e0 | leanprover-community/import-graph | Apache-2.0 | `sources/SHA256SUMS` |
| LeanSearchClient | 4fb58e749ef3fc0395fe274f6cab70c2ea85f1c9 | leanprover-community/LeanSearchClient | Apache-2.0 | `sources/SHA256SUMS` |
| plausible | 054b228ce0ac61d767c6e71ba73a24728f191b72 | leanprover-community/plausible | Apache-2.0 | `sources/SHA256SUMS` |
| Cli | 50810f72af7618bee62fe9800dc26e806c188703 | leanprover/lean4-cli | Apache-2.0 | `sources/SHA256SUMS` |
| Prebuilt oleans (payload) | built by Mathlib CI for the rev above, fetched with `cache get` from https://cache.mathlib.org/mathlib4-master (9117 files), re-packed as `tar */.lake/build` | – | as sources | c4dd7146385bee25492379810cc48b9b27689ac1bdc28c75afc5b347c4a26fff (`vendor/payload/prebuilt-oleans.tar.zst`, 2.0 GB, NOT committed) |

The dependency revs are those of Mathlib's own `lake-manifest.json` at the pinned commit.
The dependency tarballs are GitHub archive tarballs re-packed deterministically (sorted, uid 0, mtime 0).
No git submodules, no LFS, no network use at build time. Mathlib is never compiled from source.

## Size blocker
The Lean toolchain (607 MB compressed / 3.1 GB unpacked) and the prebuilt Mathlib oleans
(2.0 GB compressed / 7 GB unpacked) are ordinary files but too large to commit in this
submission. They are therefore reproduced by `scripts/bootstrap.sh` (download, sha256-checked for the
toolchain) or taken from `vendor/payload/` when present. A machine with NO network that receives only the
committed files cannot run the build: **offline rebuild from the committed files alone is UNVERIFIED / blocked**.
Offline rebuild with `vendor/payload/` supplied is verified (logs/offline-check.log).

## Update after bundle-size rejection (8 MiB limit)
The earlier submission shipped vendored sources, toolchain and oleans (6 GB) and was rejected. Now only
this file, `LEAN-LICENSE` and `sources/SHA256SUMS.repacked` (hashes of the repacked tarballs, which are NOT shipped;
the mathlib tarball alone is 24 MB) are committed. `scripts/bootstrap.sh` downloads the pinned-rev archives from
codeload.github.com (no hash check possible for GitHub archives; revs are exact commits), the Lean toolchain
(sha256-checked) and the Mathlib cache. **The offline-from-committed-files requirement cannot be met within the
8 MiB bundle limit: UNVERIFIED / blocked.** The download-based sources path of bootstrap.sh was not re-run after this change (UNVERIFIED).
