#!/usr/bin/env bash
# Full check: banned tokens, build, axioms. Run from repo root: formalization/scripts/check_all.sh
D="$(dirname "${BASH_SOURCE[0]}")"
"$D/build.sh" && "$D/axioms.sh"
