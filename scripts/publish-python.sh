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
python_command=${PYTHON:-python3}
work_dir=$(mktemp -d "${TMPDIR:-/tmp}/longshot-protocol-python-release.XXXXXX")
trap 'rm -rf "$work_dir"' EXIT
artifact_dir="$work_dir/artifacts"

LONGSHOT_PROTOCOL_PACKAGE_OUTPUT_DIR="$artifact_dir" \
  bash "$protocol_root/scripts/check-package-archives.sh"
wheels=()
sdists=()
shopt -s nullglob
wheels=("$artifact_dir"/longshot_protocol-*.whl)
sdists=("$artifact_dir"/longshot_protocol-*.tar.gz)
shopt -u nullglob
if [[ ${#wheels[@]} != 1 || ! -f "${wheels[0]}" \
  || ${#sdists[@]} != 1 || ! -f "${sdists[0]}" ]]; then
  echo "package audit emitted ${#wheels[@]} wheels and ${#sdists[@]} source archives; expected one each" >&2
  exit 1
fi

if [[ "$mode" == "--publish" ]]; then
  if ! "$python_command" -c 'import twine' 2>/dev/null; then
    echo "Python publication requires twine in the selected Python environment" >&2
    exit 1
  fi
  "$python_command" -m twine upload \
    "${wheels[0]}" \
    "${sdists[0]}"
else
  echo "Python packages are ready to publish from the exact audited archives"
fi
