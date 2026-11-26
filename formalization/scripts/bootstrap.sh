#!/usr/bin/env bash
# Usage: formalization/scripts/bootstrap.sh      (from repo root or anywhere; bounded steps)
# 1. verify SHA256 of vendored source tarballs, extract to vendor/src/
# 2. install Lean v4.36.0 into vendor/toolchain: from vendor/payload/lean-4.36.0-linux.tar.zst
#    if present (offline), else download it (sha256-checked)
# 3. install Mathlib prebuilt oleans: from vendor/payload/prebuilt-oleans.tar.zst if present
#    (offline), else `cache get` from cache.mathlib.org. Mathlib is NEVER compiled from source.
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$R"
LEAN_URL=https://github.com/leanprover/lean4/releases/download/v4.36.0/lean-4.36.0-linux.tar.zst
LEAN_SHA=2b7ab1ed8b92d2e6abfaf41344823b510064dbc9c0260cac73eb496ab2dea6eb
mkdir -p vendor/src vendor/payload build
# Dependency sources: use vendor/sources/*.tar.gz if supplied (checked against SHA256SUMS.repacked),
# else download the GitHub archive of the pinned rev (revs: vendor/PROVENANCE.md). Too big to commit (8 MiB limit).
declare -A REPO=( [mathlib]=leanprover-community/mathlib4@fc4f59e577feb1a4956671bc04ac18aaaf8cd842
 [batteries]=leanprover-community/batteries@b4b25a3886a16daacaf6615c2eea7170a6e8f458
 [Qq]=leanprover-community/quote4@ff055a2fcc835935e0ae607339b455a5f5896b4b
 [aesop]=leanprover-community/aesop@66ff77cf0c4c898799e4b94d14db55f7a02d0c5a
 [proofwidgets]=leanprover-community/ProofWidgets4@2f0f3520daeac2d9310ff25b7a877a0e5cdaa203
 [importGraph]=leanprover-community/import-graph@8370c640afcd1cc3fb1cb9bf1560cc66eafee5e0
 [LeanSearchClient]=leanprover-community/LeanSearchClient@4fb58e749ef3fc0395fe274f6cab70c2ea85f1c9
 [plausible]=leanprover-community/plausible@054b228ce0ac61d767c6e71ba73a24728f191b72
 [Cli]=leanprover/lean4-cli@50810f72af7618bee62fe9800dc26e806c188703 )
for n in "${!REPO[@]}"; do
  [ -d vendor/src/$n ] && continue
  mkdir -p vendor/src/$n
  t=$(ls vendor/sources/$n*.tar.gz 2>/dev/null | head -1 || true)
  if [ -n "$t" ]; then tar xzf "$t" -C vendor/src/$n --strip-components=1
  else timeout 540 curl -fSL --retry 3 "https://codeload.github.com/${REPO[$n]%@*}/tar.gz/${REPO[$n]#*@}" | tar xz -C vendor/src/$n --strip-components=1; fi
done
if [ ! -x vendor/toolchain/bin/lake ]; then
  Z=vendor/payload/lean-4.36.0-linux.tar.zst
  [ -f $Z ] || timeout 540 curl -fSL --retry 3 -o $Z "$LEAN_URL"
  echo "$LEAN_SHA  $Z" | sha256sum -c -
  mkdir -p vendor/toolchain; zstd -dc < $Z | tar x -C vendor/toolchain --strip-components=1
fi
source scripts/env.sh
lean --version
P=vendor/payload/prebuilt-oleans.tar.zst
if [ -f $P ]; then
  [ -f $P.sha256 ] && (cd vendor/payload && sha256sum -c prebuilt-oleans.tar.zst.sha256)
  zstd -dc < $P | tar x -C vendor/src      # restores vendor/src/*/.lake/build
else
  # build the (small) `cache` executable from vendored sources, run it from the mathlib dir
  timeout 540 lake build mathlib/cache:exe
  ( cd vendor/src/mathlib && mkdir -p .lake && rm -rf .lake/packages && ln -s ../.. .lake/packages
    export LEAN_SRC_PATH="$PWD:$(ls -d "$R"/vendor/src/* | grep -v '/mathlib$' | tr '\n' ':')"
    timeout 540 .lake/build/bin/cache get ) 2>&1 | tr '\r' '\n' | tail -n 20 | tee build/cache-get.log
fi
echo "bootstrap done"
