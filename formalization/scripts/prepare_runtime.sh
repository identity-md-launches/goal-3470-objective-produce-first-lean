#!/usr/bin/env bash
set -euo pipefail
D="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec timeout --signal=TERM --kill-after=5s 530s python3 -I -B "$D/prepare_runtime.py" "$@"
