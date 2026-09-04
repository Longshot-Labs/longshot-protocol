#!/usr/bin/env bash
set -euo pipefail

protocol_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source_guide="$protocol_root/CUSTOM_CLIENTS.md"
copies=(
  "$protocol_root/rust/CUSTOM_CLIENTS.md"
  "$protocol_root/typescript/CUSTOM_CLIENTS.md"
  "$protocol_root/python/src/longshot_protocol/CUSTOM_CLIENTS.md"
)

for copy in "${copies[@]}"; do
  if ! cmp -s "$source_guide" "$copy"; then
    echo "custom client guide is stale: ${copy#"$protocol_root"/}" >&2
    exit 1
  fi
done

echo "public packages contain the current CUSTOM_CLIENTS.md"
