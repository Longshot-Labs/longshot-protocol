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
source_dir="$protocol_root/rust"
bash "$protocol_root/scripts/check-public-surface.sh" --auto

work_dir=$(mktemp -d "${TMPDIR:-/tmp}/longshot-protocol-rust.XXXXXX")
trap 'rm -rf "$work_dir"' EXIT

export_dir="$work_dir/export"
mkdir -p "$export_dir"
tar -C "$source_dir" -cf - Cargo.toml README.md CUSTOM_CLIENTS.md LICENSE.txt src \
  | tar -C "$export_dir" -xf -

awk '
  /^publish = false$/ { print "publish = [\"crates-io\"]"; next }
  { print }
' "$export_dir/Cargo.toml" > "$export_dir/Cargo.toml.next"
mv "$export_dir/Cargo.toml.next" "$export_dir/Cargo.toml"
grep -Fqx 'publish = ["crates-io"]' "$export_dir/Cargo.toml"

export CARGO_TARGET_DIR="$work_dir/target"
cargo package --manifest-path "$export_dir/Cargo.toml"

archives=()
shopt -s nullglob
archives=("$CARGO_TARGET_DIR/package"/longshot-protocol-*.crate)
shopt -u nullglob
if [[ ${#archives[@]} != 1 || ! -f "${archives[0]}" ]]; then
  echo "cargo produced ${#archives[@]} longshot-protocol archives; expected one" >&2
  exit 1
fi
archive=${archives[0]}
archive_listing="$work_dir/archive-list.txt"
tar -tzf "$archive" > "$archive_listing"
if grep -Eq '/\.cargo_vcs_info\.json$' "$archive_listing"; then
  echo "Rust package contains repository-only metadata" >&2
  exit 1
fi
if ! grep -Eq '/CUSTOM_CLIENTS\.md$' "$archive_listing"; then
  echo "Rust package is missing CUSTOM_CLIENTS.md" >&2
  exit 1
fi
mkdir "$work_dir/archive"
tar -xzf "$archive" -C "$work_dir/archive"
"${PYTHON:-python3}" "$protocol_root/scripts/check-archive-secrets.py" "$work_dir/archive"

if [[ -n "${LONGSHOT_PROTOCOL_RUST_ARCHIVE_OUTPUT:-}" ]]; then
  cp "$archive" "$LONGSHOT_PROTOCOL_RUST_ARCHIVE_OUTPUT"
fi

if [[ "$mode" == "--publish" ]]; then
  cargo publish --manifest-path "$export_dir/Cargo.toml"
else
  echo "Rust package is publishable, includes CUSTOM_CLIENTS.md, and excludes repository-only metadata"
fi
