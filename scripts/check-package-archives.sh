#!/usr/bin/env bash
set -euo pipefail

protocol_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
python_command=${PYTHON:-python3}

for command_name in cargo npm pnpm tar unzip "$python_command"; do
  if ! command -v "$command_name" >/dev/null; then
    echo "package archive audit requires $command_name" >&2
    exit 1
  fi
done
if ! "$python_command" -c 'import build' 2>/dev/null; then
  echo "package archive audit requires the Python build package" >&2
  exit 1
fi

bash "$protocol_root/scripts/check-custom-client-guide.sh"
"$python_command" "$protocol_root/scripts/check-archive-secrets.py" --self-test

work_dir=$(mktemp -d "${TMPDIR:-/tmp}/longshot-protocol-packages.XXXXXX")
trap 'rm -rf "$work_dir"' EXIT
artifact_dir="$work_dir/artifacts"
mkdir -p "$artifact_dir"

python_source="$work_dir/python-source"
mkdir -p "$python_source"
cp \
  "$protocol_root/python/LICENSE.txt" \
  "$protocol_root/python/MANIFEST.in" \
  "$protocol_root/python/README.md" \
  "$protocol_root/python/pyproject.toml" \
  "$python_source/"
cp -R "$protocol_root/python/src" "$python_source/"

typescript_source="$work_dir/typescript-source"
mkdir -p "$typescript_source"
npm --prefix "$protocol_root/typescript" run build
cp \
  "$protocol_root/typescript/CUSTOM_CLIENTS.md" \
  "$protocol_root/typescript/LICENSE.txt" \
  "$protocol_root/typescript/README.md" \
  "$protocol_root/typescript/package.json" \
  "$typescript_source/"
cp -R "$protocol_root/typescript/dist" "$typescript_source/"
node --input-type=module - "$typescript_source/package.json" <<'NODE'
import { readFileSync, writeFileSync } from "node:fs";

const path = process.argv[2];
const packageJson = JSON.parse(readFileSync(path, "utf8"));
if (packageJson.private !== true || Object.hasOwn(packageJson, "version"))
  throw new Error("TypeScript source manifest must remain private and omit version");
if (typeof packageJson.longshotReleaseVersion !== "string" || !packageJson.longshotReleaseVersion)
  throw new Error("TypeScript source manifest has no release version");
packageJson.version = packageJson.longshotReleaseVersion;
delete packageJson.longshotReleaseVersion;
packageJson.private = false;
delete packageJson.scripts;
writeFileSync(path, `${JSON.stringify(packageJson, null, 2)}\n`);
NODE

rust_archive="$artifact_dir/longshot-protocol.crate"
LONGSHOT_PROTOCOL_RUST_ARCHIVE_OUTPUT="$rust_archive" \
  bash "$protocol_root/scripts/publish-rust.sh" --check
npm pack "$typescript_source" --pack-destination "$artifact_dir" --json \
  > "$work_dir/npm-pack.json"
"$python_command" -m build --wheel --sdist --outdir "$artifact_dir" \
  "$python_source"

find_one_file() {
  local directory=$1
  local pattern=$2
  local label=$3
  local matches=()
  shopt -s nullglob
  matches=("$directory"/$pattern)
  shopt -u nullglob
  if [[ ${#matches[@]} != 1 || ! -f "${matches[0]}" ]]; then
    echo "expected one $label artifact, found ${#matches[@]}" >&2
    exit 1
  fi
  printf '%s\n' "${matches[0]}"
}

find_one_directory() {
  local directory=$1
  local label=$2
  local matches=()
  shopt -s nullglob
  matches=("$directory"/*)
  shopt -u nullglob
  if [[ ${#matches[@]} != 1 || ! -d "${matches[0]}" ]]; then
    echo "expected one extracted $label directory, found ${#matches[@]}" >&2
    exit 1
  fi
  printf '%s\n' "${matches[0]}"
}

typescript_archive=$(find_one_file "$artifact_dir" 'longshot-protocol-*.tgz' TypeScript)
python_wheel=$(find_one_file "$artifact_dir" 'longshot_protocol-*.whl' 'Python wheel')
python_sdist=$(find_one_file "$artifact_dir" 'longshot_protocol-*.tar.gz' 'Python sdist')

rust_listing="$work_dir/rust.list"
typescript_listing="$work_dir/typescript.list"
python_wheel_listing="$work_dir/python-wheel.list"
python_sdist_listing="$work_dir/python-sdist.list"
tar -tzf "$rust_archive" > "$rust_listing"
tar -tzf "$typescript_archive" > "$typescript_listing"
unzip -Z1 "$python_wheel" > "$python_wheel_listing"
tar -tzf "$python_sdist" > "$python_sdist_listing"

"$python_command" - "$rust_listing" "$protocol_root/rust/src" <<'PY'
from pathlib import Path
import sys

listing = Path(sys.argv[1])
source_root = Path(sys.argv[2])
expected = {
    "Cargo.lock",
    "Cargo.toml",
    "Cargo.toml.orig",
    "CUSTOM_CLIENTS.md",
    "LICENSE.txt",
    "README.md",
}
expected.update(
    f"src/{path.relative_to(source_root).as_posix()}"
    for path in source_root.rglob("*")
    if path.is_file()
)
actual = set()
for entry in listing.read_text(encoding="utf-8").splitlines():
    if not entry or entry.endswith("/"):
        continue
    parts = entry.split("/", 1)
    if len(parts) != 2:
        raise SystemExit(f"Rust archive has an invalid path: {entry}")
    actual.add(parts[1])
extra = sorted(actual - expected)
missing = sorted(expected - actual)
if extra or missing:
    raise SystemExit(
        "closed packed Rust file inventory drift: "
        f"extra=[{', '.join(extra)}], missing=[{', '.join(missing)}]"
    )
PY

"$python_command" - "$typescript_listing" <<'PY'
from pathlib import Path
import sys

modules = {
    "api",
    "bytes",
    "index",
    "mm",
    "model",
    "rfq",
    "serde",
    "serde.generated",
    "taker",
    "types",
    "uuid",
    "ws",
}
expected = {
    "package/CUSTOM_CLIENTS.md",
    "package/LICENSE.txt",
    "package/README.md",
    "package/package.json",
}
for module in modules:
    expected.add(f"package/dist/src/{module}.js")
    expected.add(f"package/dist/src/{module}.d.ts")
actual = {
    entry.strip()
    for entry in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
    if entry.strip() and not entry.endswith("/")
}
extra = sorted(actual - expected)
missing = sorted(expected - actual)
if extra or missing:
    raise SystemExit(
        "closed packed TypeScript file inventory drift: "
        f"extra=[{', '.join(extra)}], missing=[{', '.join(missing)}]"
    )
PY

"$python_command" - \
  "$python_wheel_listing" \
  "$python_sdist_listing" \
  "$protocol_root/python/src" <<'PY'
from pathlib import Path
import sys

wheel_listing = Path(sys.argv[1])
sdist_listing = Path(sys.argv[2])
source_root = Path(sys.argv[3])
package_files = {
    path.relative_to(source_root).as_posix()
    for path in source_root.rglob("*")
    if path.is_file()
    and "__pycache__" not in path.relative_to(source_root).parts
    and path.suffix not in {".pyc", ".pyo"}
}

wheel_actual = {
    entry.strip()
    for entry in wheel_listing.read_text(encoding="utf-8").splitlines()
    if entry.strip() and not entry.endswith("/")
}
dist_info_roots = {
    entry.split("/", 1)[0]
    for entry in wheel_actual
    if ".dist-info/" in entry
}
if len(dist_info_roots) != 1:
    raise SystemExit("Python wheel must contain exactly one dist-info directory")
dist_info = next(iter(dist_info_roots))
wheel_expected = package_files | {
    f"{dist_info}/METADATA",
    f"{dist_info}/RECORD",
    f"{dist_info}/WHEEL",
    f"{dist_info}/licenses/LICENSE.txt",
    f"{dist_info}/top_level.txt",
}
wheel_extra = sorted(wheel_actual - wheel_expected)
wheel_missing = sorted(wheel_expected - wheel_actual)
if wheel_extra or wheel_missing:
    raise SystemExit(
        "closed Python wheel file inventory drift: "
        f"extra=[{', '.join(wheel_extra)}], missing=[{', '.join(wheel_missing)}]"
    )

sdist_entries = {
    entry.strip()
    for entry in sdist_listing.read_text(encoding="utf-8").splitlines()
    if entry.strip() and not entry.endswith("/")
}
sdist_roots = {entry.split("/", 1)[0] for entry in sdist_entries}
if len(sdist_roots) != 1:
    raise SystemExit("Python sdist must contain exactly one root directory")
sdist_root = next(iter(sdist_roots))
sdist_actual = {
    entry.split("/", 1)[1]
    for entry in sdist_entries
    if entry.startswith(f"{sdist_root}/")
}
sdist_expected = {
    "LICENSE.txt",
    "MANIFEST.in",
    "PKG-INFO",
    "README.md",
    "pyproject.toml",
    "setup.cfg",
    "src/longshot_protocol.egg-info/PKG-INFO",
    "src/longshot_protocol.egg-info/SOURCES.txt",
    "src/longshot_protocol.egg-info/dependency_links.txt",
    "src/longshot_protocol.egg-info/requires.txt",
    "src/longshot_protocol.egg-info/top_level.txt",
}
sdist_expected.update(f"src/{path}" for path in package_files)
sdist_extra = sorted(sdist_actual - sdist_expected)
sdist_missing = sorted(sdist_expected - sdist_actual)
if sdist_extra or sdist_missing:
    raise SystemExit(
        "closed Python sdist file inventory drift: "
        f"extra=[{', '.join(sdist_extra)}], missing=[{', '.join(sdist_missing)}]"
    )
PY

reject_unsafe_archive_paths() {
  local label=$1
  local listing=$2
  local forbidden='(^/|(^|/)\.\.(/|$)|(^|/)(fixtures?|tests?|examples?|scripts?|tools?|\.github|__pycache__)(/|$)|(^|/)\.(git[^/]*|hg|svn)(/|$)|(^|/)(AGENTS\.md|package-lock\.json|pnpm-lock\.yaml|pnpm-workspace\.yaml|tsconfig\.json|\.cargo_vcs_info\.json|\.editorconfig)$|(^|/)[^/]*\.py[co]$|(^|/)(generate|generator)[^/]*(\.[^/]*)?$|(^|/)[^/]*openapi[^/]*(/|$))'
  if grep -E -i "$forbidden" "$listing"; then
    echo "$label archive contains a private or repository-only path" >&2
    exit 1
  fi
}

reject_unsafe_archive_paths "Rust" "$rust_listing"
reject_unsafe_archive_paths "TypeScript" "$typescript_listing"
reject_unsafe_archive_paths "Python wheel" "$python_wheel_listing"
reject_unsafe_archive_paths "Python sdist" "$python_sdist_listing"

rust_extract="$work_dir/rust"
typescript_extract="$work_dir/typescript"
python_wheel_extract="$work_dir/python-wheel"
python_sdist_extract="$work_dir/python-sdist"
mkdir -p "$rust_extract" "$typescript_extract" "$python_wheel_extract" "$python_sdist_extract"
tar -xzf "$rust_archive" -C "$rust_extract"
tar -xzf "$typescript_archive" -C "$typescript_extract"
unzip -q "$python_wheel" -d "$python_wheel_extract"
tar -xzf "$python_sdist" -C "$python_sdist_extract"

rust_root=$(find_one_directory "$rust_extract" Rust)
typescript_root="$typescript_extract/package"
python_sdist_root=$(find_one_directory "$python_sdist_extract" 'Python sdist')

"$python_command" - \
  "$protocol_root/python" \
  "$python_wheel_extract" \
  "$python_sdist_root" <<'PY'
from pathlib import Path
import sys

source_root = Path(sys.argv[1])
wheel_root = Path(sys.argv[2])
sdist_root = Path(sys.argv[3])
package_source = source_root / "src"
for source in package_source.rglob("*"):
    relative = source.relative_to(package_source)
    if (
        not source.is_file()
        or "__pycache__" in relative.parts
        or source.suffix in {".pyc", ".pyo"}
    ):
        continue
    expected = source.read_bytes()
    wheel_path = wheel_root / relative
    sdist_path = sdist_root / "src" / relative
    if not wheel_path.is_file() or wheel_path.read_bytes() != expected:
        raise SystemExit(f"Python wheel package bytes drifted: {relative.as_posix()}")
    if not sdist_path.is_file() or sdist_path.read_bytes() != expected:
        raise SystemExit(f"Python sdist package bytes drifted: {relative.as_posix()}")
for name in ["LICENSE.txt", "MANIFEST.in", "README.md", "pyproject.toml"]:
    source = source_root / name
    packed = sdist_root / name
    if not packed.is_file() or packed.read_bytes() != source.read_bytes():
        raise SystemExit(f"Python sdist release bytes drifted: {name}")
PY

"$python_command" - \
  "$protocol_root/rust/Cargo.toml" \
  "$rust_root/Cargo.toml.orig" <<'PY'
from pathlib import Path
import sys

expected = Path(sys.argv[1]).read_text(encoding="utf-8").replace(
    'publish = false\n',
    'publish = ["crates-io"]\n',
)
actual = Path(sys.argv[2]).read_text(encoding="utf-8")
if actual != expected:
    raise SystemExit("packed Rust manifest drifted from the audited release manifest")
PY

"$python_command" - \
  "$typescript_root/package.json" \
  "$typescript_root" \
  "$protocol_root/typescript/package.json" <<'PY'
import json
from pathlib import Path
import sys

manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
root = Path(sys.argv[2]).resolve()
source_manifest = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
release_version = source_manifest.pop("longshotReleaseVersion", None)
if not isinstance(release_version, str) or not release_version:
    raise SystemExit("source TypeScript manifest has no release version")
source_manifest["version"] = release_version
source_manifest["private"] = False
source_manifest.pop("scripts", None)
if manifest != source_manifest:
    raise SystemExit("packed TypeScript manifest drifted from the audited release manifest")

def validate(label: str, target: object, suffix: str) -> None:
    if not isinstance(target, str) or not target.startswith("./") or not target.endswith(suffix):
        raise SystemExit(f"packed TypeScript {label} has an invalid target")
    path = (root / target).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise SystemExit(f"packed TypeScript {label} target is missing or unsafe: {target}")

validate("main", manifest.get("main"), ".js")
validate("types", manifest.get("types"), ".d.ts")
exports = manifest.get("exports")
if not isinstance(exports, dict) or not exports:
    raise SystemExit("packed TypeScript package has no exports map")
for name, conditions in exports.items():
    if not isinstance(conditions, dict):
        raise SystemExit(f"packed TypeScript export {name} is not conditional")
    validate(f"export {name} import", conditions.get("import"), ".js")
    validate(f"export {name} types", conditions.get("types"), ".d.ts")
print("Packed TypeScript main, types, and exports targets are valid")
PY

"$python_command" "$protocol_root/scripts/check-archive-secrets.py" \
  "$rust_extract" "$typescript_extract" "$python_wheel_extract" "$python_sdist_extract"

smoke_test_python_wheel() {
  local label=$1
  local wheel=$2
  local venv="$work_dir/python-$label-venv"
  "$python_command" -m venv "$venv"
  "$venv/bin/python" -m pip install --disable-pip-version-check \
    --force-reinstall "$wheel" >/dev/null
  "$venv/bin/python" -I - <<'PY'
import importlib
from pathlib import Path
import sys

package = importlib.import_module("longshot_protocol")
if not Path(package.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()):
    raise SystemExit("longshot_protocol imported outside the audit environment")
for module in ("api", "mm", "model", "rfq", "taker", "types", "ws"):
    importlib.import_module(f"longshot_protocol.{module}")
for symbol in (
    "BroadcastRfqRequest",
    "CommunityPickMode",
    "CommunityPickRequest",
    "CreateRfqRequest",
    "CreateUnsignedRfqRequest",
    "ProfitCapConfigResponse",
    "ProfitCapOverrideResponse",
):
    if not hasattr(package, symbol):
        raise SystemExit(f"packed Python package is missing {symbol}")
print("Packed Python package imports all runtime modules and required contracts")
PY
}

smoke_test_python_wheel wheel "$python_wheel"
sdist_wheel_dir="$work_dir/python-sdist-wheel"
mkdir -p "$sdist_wheel_dir"
"$python_command" -m build --wheel --outdir "$sdist_wheel_dir" "$python_sdist_root" >/dev/null
sdist_wheel=$(find_one_file "$sdist_wheel_dir" '*.whl' 'rebuilt Python sdist wheel')
smoke_test_python_wheel sdist "$sdist_wheel"

surface_root="$work_dir/public-surface"
mkdir -p \
  "$surface_root/rust" \
  "$surface_root/typescript/src" \
  "$surface_root/typescript/scripts" \
  "$surface_root/typescript/tests" \
  "$surface_root/python/src" \
  "$surface_root/python/tools" \
  "$surface_root/python/tests" \
  "$surface_root/rust/tests" \
  "$surface_root/fixtures/api" \
  "$surface_root/scripts"
cp -R "$rust_root/src" "$surface_root/rust/"
cp "$rust_root/README.md" "$rust_root/CUSTOM_CLIENTS.md" "$surface_root/rust/"
while IFS= read -r -d '' wheel_entry; do
  wheel_entry_name=$(basename "$wheel_entry")
  case "$wheel_entry_name" in
    *.data | *.dist-info) continue ;;
  esac
  cp -R "$wheel_entry" "$surface_root/python/src/"
done < <(find "$python_wheel_extract" -mindepth 1 -maxdepth 1 -print0)
cp \
  "$python_sdist_root/LICENSE.txt" \
  "$python_sdist_root/MANIFEST.in" \
  "$python_sdist_root/README.md" \
  "$python_sdist_root/pyproject.toml" \
  "$surface_root/python/"
cp \
  "$typescript_root/README.md" \
  "$typescript_root/CUSTOM_CLIENTS.md" \
  "$typescript_root/package.json" \
  "$surface_root/typescript/"
cp "$rust_root/README.md" "$surface_root/README.md"
cp "$rust_root/CUSTOM_CLIENTS.md" "$surface_root/CUSTOM_CLIENTS.md"
cp "$protocol_root/fixtures/api/openapi.json" "$surface_root/fixtures/api/"
cp \
  "$protocol_root/scripts/check-archive-secrets.py" \
  "$protocol_root/scripts/check-public-surface.sh" \
  "$surface_root/scripts/"
cp \
  "$protocol_root/python/tools/generate_api_stub.py" \
  "$protocol_root/python/tools/generate_serde_metadata.py" \
  "$surface_root/python/tools/"
cp \
  "$protocol_root/typescript/scripts/generate-serde.mjs" \
  "$protocol_root/typescript/scripts/public-openapi-contract.mjs" \
  "$surface_root/typescript/scripts/"
ln -s "$protocol_root/typescript/node_modules" "$surface_root/typescript/node_modules"

while IFS= read -r -d '' packed_source; do
  relative=${packed_source#"$typescript_root/dist/src/"}
  destination="$surface_root/typescript/src/$relative"
  if [[ "$destination" == *.d.ts ]]; then
    destination=${destination%.d.ts}.ts
  fi
  mkdir -p "$(dirname "$destination")"
  cp "$packed_source" "$destination"
done < <(find "$typescript_root/dist/src" -type f \
  \( -name '*.js' -o -name '*.mjs' -o -name '*.cjs' -o -name '*.d.ts' \) -print0)

archive_contents="$surface_root/typescript/src/archive-contents.audit"
# The packed language trees prove executable contracts. This extra lexical input
# also scans release metadata and documentation that those trees do not copy.
: > "$archive_contents"
for extract_root in "$rust_extract" "$typescript_extract" "$python_wheel_extract" "$python_sdist_extract"; do
  while IFS= read -r -d '' archive_file; do
    printf '\n%s\n' "$archive_file" >> "$archive_contents"
    cat "$archive_file" >> "$archive_contents"
  done < <(find "$extract_root" -type f -print0)
done
bash "$surface_root/scripts/check-public-surface.sh" --authoritative --packed

npm_audit_root="$work_dir/npm-audit"
mkdir -p "$npm_audit_root"
(
  cd "$npm_audit_root"
  pnpm add "$typescript_archive" --prod --ignore-scripts
  pnpm audit --prod --audit-level high
  node --input-type=module -e \
    'await import("longshot-protocol"); console.log("Packed TypeScript root entry point imports successfully")'
)

if [[ -n "${LONGSHOT_PROTOCOL_PACKAGE_OUTPUT_DIR:-}" ]]; then
  mkdir -p "$LONGSHOT_PROTOCOL_PACKAGE_OUTPUT_DIR"
  output_dir=$(cd "$LONGSHOT_PROTOCOL_PACKAGE_OUTPUT_DIR" && pwd)
  artifacts=("$rust_archive" "$typescript_archive" "$python_wheel" "$python_sdist")
  destinations=()
  for artifact in "${artifacts[@]}"; do
    destination="$output_dir/$(basename "$artifact")"
    if [[ -e "$destination" ]]; then
      echo "refusing to overwrite package artifact: $destination" >&2
      exit 1
    fi
    destinations+=("$destination")
  done
  for index in "${!artifacts[@]}"; do
    cp "${artifacts[$index]}" "${destinations[$index]}"
  done
  echo "Audited package archives copied to $output_dir"
fi

echo "Rust, TypeScript, Python wheel, and Python sdist archives contain only the audited public package surface"
