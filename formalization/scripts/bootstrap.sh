#!/usr/bin/env bash
# Every entry point is bounded, fail-closed, and accepts --runtime DIR.
set -euo pipefail
D="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec timeout --signal=TERM --kill-after=5s 530s python3 -I -B "$D/harness.py" bootstrap "$@"
