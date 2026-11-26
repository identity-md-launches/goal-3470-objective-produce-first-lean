#!/usr/bin/env bash
# Fresh-copy, no-network, clean-environment test of the whole recipe.
# Usage: formalization/scripts/offline_test.sh [PAYLOAD_DIR]
#   Copies only the deliverable files (git-tracked/untracked-not-ignored under formalization/) to a
#   new temp dir, adds PAYLOAD_DIR (default vendor/payload: toolchain tarball + prebuilt oleans, NOT
#   committed because of size) if it exists, adds a temporary smoke module, runs bootstrap, build,
#   axioms with networking disabled (unshare -rn, falling back to stripped proxy env) and prints exit codes.
set -uo pipefail
S="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAY="${1:-$S/vendor/payload}"
T="$(mktemp -d -p "${OFFLINE_TMP:-${TMPDIR:-/tmp}}")"; trap 'rm -rf "$T"' EXIT
(cd "$S/.." && git ls-files -co --exclude-standard formalization -z | grep -zv '^formalization/build/' | tar --null -T - -cf -) | tar -xf - -C "$T"
W="$T/formalization"; mkdir -p "$W/vendor/payload"
for f in "$PAY"/*; do [ -e "$f" ] && ln -s "$f" "$W/vendor/payload/"; done
mkdir -p "$W/MissingTheorems/Target01/RouteA" "$W/MissingTheorems/Target08/RouteB"
cp "$S/MissingTheorems/Target01/RouteA/Smoke.lean" "$W/MissingTheorems/Target01/RouteA/Smoke.lean" 2>/dev/null || cat > "$W/MissingTheorems/Target01/RouteA/Smoke.lean" <<'L'
import Mathlib.Tactic.Ring
/-! Temporary smoke module. -/
namespace MissingTheorems.Target01.RouteA
theorem smoke_add_comm (a b : ℕ) : a + b = b + a := by ring
end MissingTheorems.Target01.RouteA
L
cat > "$W/MissingTheorems/Target08/RouteB/Smoke.lean" <<'L'
import Mathlib.Tactic.Ring
/-! Temporary smoke module. -/
namespace MissingTheorems.Target08.RouteB
theorem smoke_mul_comm (a b : ℕ) : a * b = b * a := by ring
end MissingTheorems.Target08.RouteB
L
cat > "$W/manifest/smoke_declarations.json" <<'L'
{"declarations": [{"name": "MissingTheorems.Target01.RouteA.smoke_add_comm", "module": "MissingTheorems.Target01.RouteA.Smoke"},
 {"name": "MissingTheorems.Target08.RouteB.smoke_mul_comm", "module": "MissingTheorems.Target08.RouteB.Smoke"}]}
L
DEAD=http://127.0.0.1:9   # no user namespaces here for `unshare -rn`: send all proxied traffic to a dead port
NETENV=(http_proxy=$DEAD https_proxy=$DEAD HTTP_PROXY=$DEAD HTTPS_PROXY=$DEAD ALL_PROXY=$DEAD)
unshare -rn true 2>/dev/null && NONET="unshare -rn" || NONET=""
echo "network isolation: ${NONET:-dead-proxy only (kernel forbids netns; UNVERIFIED as true isolation)}"
run() { env -i PATH=/usr/bin:/bin "${NETENV[@]}" $NONET "$@"; }
( run curl -sS -m 5 -o /dev/null https://github.com && echo "NETWORK STILL REACHABLE" || echo "network unreachable (good)" ) 2>&1 | tail -1
cd "$W"
run bash scripts/bootstrap.sh; echo "bootstrap exit=$?"
run bash scripts/build.sh | tail -3; echo "build exit=${PIPESTATUS[0]}"
run bash scripts/axioms.sh --manifest manifest/smoke_declarations.json; echo "axioms exit=$?"
run bash scripts/axioms.sh | tail -2; echo "axioms (real manifest) exit=$?"
