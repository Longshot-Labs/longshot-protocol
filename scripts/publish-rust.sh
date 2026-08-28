#!/usr/bin/env bash
set -euo pipefail

mode=${1:---check}
if [[ "$mode" != "--check" && "$mode" != "--publish" ]]; then
  echo "usage: $0 [--check|--publish]" >&2
  exit 2
fi

protocol_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source_dir="$protocol_root/rust"
bash "$protocol_root/scripts/check-public-surface.sh"

work_dir=$(mktemp -d "${TMPDIR:-/tmp}/longshot-protocol-rust.XXXXXX")
trap 'rm -rf "$work_dir"' EXIT

export_dir="$work_dir/export"
mkdir -p "$export_dir"
tar -C "$source_dir" -cf - Cargo.toml README.md LICENSE.txt src \
  | tar -C "$export_dir" -xf -

awk '
  /^publish = false$/ { print "publish = [\"crates-io\"]"; next }
  { print }
' "$export_dir/Cargo.toml" > "$export_dir/Cargo.toml.next"
mv "$export_dir/Cargo.toml.next" "$export_dir/Cargo.toml"
grep -Fqx 'publish = ["crates-io"]' "$export_dir/Cargo.toml"

export CARGO_TARGET_DIR="$work_dir/target"
cargo package --manifest-path "$export_dir/Cargo.toml"

archive=$(find "$CARGO_TARGET_DIR/package" -maxdepth 1 -name 'longshot-protocol-*.crate' -print -quit)
if [[ -z "$archive" ]]; then
  echo "cargo did not produce a longshot-protocol archive" >&2
  exit 1
fi
if tar -tzf "$archive" | grep -Eq '/(\.cargo_vcs_info\.json|CUSTOM_CLIENTS\.md)$'; then
  echo "Rust package contains repository-only metadata or documentation" >&2
  exit 1
fi

if [[ "$mode" == "--publish" ]]; then
  cargo publish --manifest-path "$export_dir/Cargo.toml"
else
  echo "Rust package is publishable and excludes repository-only metadata and documentation"
fi
