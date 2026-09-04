#!/usr/bin/env bash
set -euo pipefail

if [[ $# -gt 1 ]]; then
  echo "usage: $0 [--check|--publish]" >&2
  exit 2
fi
mode=${1:---check}
if [[ "$mode" != "--check" && "$mode" != "--publish" ]]; then
  echo "usage: $0 [--check|--publish]" >&2
  exit 2
fi

protocol_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
work_dir=$(mktemp -d "${TMPDIR:-/tmp}/longshot-protocol-typescript-release.XXXXXX")
trap 'rm -rf "$work_dir"' EXIT
artifact_dir="$work_dir/artifacts"

LONGSHOT_PROTOCOL_PACKAGE_OUTPUT_DIR="$artifact_dir" \
  bash "$protocol_root/scripts/check-package-archives.sh"
archives=()
shopt -s nullglob
archives=("$artifact_dir"/longshot-protocol-*.tgz)
shopt -u nullglob
if [[ ${#archives[@]} != 1 || ! -f "${archives[0]}" ]]; then
  echo "package audit emitted ${#archives[@]} TypeScript archives; expected one" >&2
  exit 1
fi
archive=${archives[0]}

if [[ "$mode" == "--publish" ]]; then
  npm publish "$archive" --access public --ignore-scripts
else
  echo "TypeScript package is ready to publish from the exact audited archive"
fi
