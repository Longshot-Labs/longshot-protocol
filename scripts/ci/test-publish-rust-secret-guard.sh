#!/usr/bin/env bash
set -euo pipefail

protocol_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
probe_root=$(mktemp -d "${TMPDIR:-/tmp}/longshot-rust-publish-probe.XXXXXX")
trap 'rm -rf "$probe_root"' EXIT
probe_protocol="$probe_root/longshot-protocol"
mkdir -p "$probe_root/bin" "$probe_protocol/scripts"
ln -s "$protocol_root/rust" "$probe_protocol/rust"
cp "$protocol_root/scripts/"{publish-rust.sh,check-archive-secrets.py} \
  "$probe_protocol/scripts/"
printf '#!/usr/bin/env bash\n[[ "$#" -eq 1 && "$1" == "--auto" ]]\n' > "$probe_protocol/scripts/check-public-surface.sh"

cat > "$probe_root/bin/cargo" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

command_name=$1
shift
printf '%s\n' "$command_name" >> "$CARGO_PROBE_LOG"
if [[ "$command_name" == "publish" ]]; then
  touch "$CARGO_PUBLISH_PROBE"
  exit 0
fi
if [[ "$command_name" != "package" || "$1" != "--manifest-path" ]]; then
  echo "unexpected cargo command: $command_name" >&2
  exit 1
fi
manifest=$2
version=$(awk -F'"' '/^version = / { print $2; exit }' "$manifest")
package="longshot-protocol-$version"
mkdir -p "$CARGO_TARGET_DIR/package/$package"
cp -R "$(dirname "$manifest")/." "$CARGO_TARGET_DIR/package/$package/"
printf '\nghp_0123456789abcdefghijklmnopqrstuvwxyzAB\n' \
  >> "$CARGO_TARGET_DIR/package/$package/README.md"
tar -C "$CARGO_TARGET_DIR/package" -czf \
  "$CARGO_TARGET_DIR/package/$package.crate" "$package"
SH
chmod +x "$probe_root/bin/cargo"

if output=$(PATH="$probe_root/bin:$PATH" \
  CARGO_PROBE_LOG="$probe_root/cargo.log" \
  CARGO_PUBLISH_PROBE="$probe_root/published" \
  bash "$probe_protocol/scripts/publish-rust.sh" --publish 2>&1); then
  echo "Rust publisher accepted a secret-bearing archive" >&2
  exit 1
fi
grep -Fq "public package contains prefixed access token" <<< "$output"
[[ $(grep -Fxc package "$probe_root/cargo.log") == 1 ]]
[[ ! -e "$probe_root/published" ]]
echo "Rust publisher blocks secret-bearing archives before publication"
