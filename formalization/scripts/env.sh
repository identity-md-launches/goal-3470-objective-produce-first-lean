#!/usr/bin/env bash
# Compatibility helper for callers; entry points use a clean subprocess allowlist.
# HOME is deliberately neither read nor reassigned. This does not bootstrap anything.
FORMAL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export FORMAL_ROOT
export PATH="$FORMAL_ROOT/vendor/toolchain/bin:/usr/bin:/bin"
export ELAN_HOME="$FORMAL_ROOT/.state/elan"
export LAKE_NO_CACHE=1 MATHLIB_NO_CACHE_ON_UPDATE=1
