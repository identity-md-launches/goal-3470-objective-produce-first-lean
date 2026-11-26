# Source me. Puts the vendored Lean toolchain on PATH; no user setup is read.
FORMAL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export FORMAL_ROOT
export PATH="$FORMAL_ROOT/vendor/toolchain/bin:/usr/bin:/bin"
export ELAN_HOME="$FORMAL_ROOT/vendor/.no-elan"
export LAKE_NO_CACHE=1 MATHLIB_NO_CACHE_ON_UPDATE=1
export HOME="${FORMAL_HOME:-$FORMAL_ROOT/.lake/home}"
mkdir -p "$HOME"
cd "$FORMAL_ROOT"
