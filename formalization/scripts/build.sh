#!/usr/bin/env bash
# Build every present proof module (all MissingTheorems.+ submodules) against the prebuilt Mathlib
# cache, after the banned-token scan. Works from the repo root: formalization/scripts/build.sh
set -uo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"
mkdir -p build
python3 -I scripts/check.py banned || exit 1
timeout 540 lake build MissingTheorems 2>&1 | tee build/build.log
exit "${PIPESTATUS[0]}"
