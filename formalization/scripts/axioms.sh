#!/usr/bin/env bash
# #print axioms for every declaration in manifest/declarations.json (or --manifest FILE).
set -uo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"
timeout 540 python3 -I scripts/check.py axioms "$@" 2>&1 | tee build/axioms.log
exit "${PIPESTATUS[0]}"
