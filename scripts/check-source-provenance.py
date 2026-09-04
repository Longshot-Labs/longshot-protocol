#!/usr/bin/env python3
"""Create and verify deterministic Longshot Protocol export provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


SOURCE_MANIFEST = "SOURCE.json"
SCHEMA_VERSION = 1
PAYLOAD_HASH_DOMAIN = b"longshot-protocol-payload-v1\0"


class ProvenanceError(RuntimeError):
    """The rendered repository does not match its provenance manifest."""


def canonical_json(value: Any) -> bytes:
    """Return the stable compact encoding used for all provenance hashes."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def validate_relative_path(raw_path: str) -> PurePosixPath:
    """Return a safe repository-relative POSIX path."""
    if (
        not isinstance(raw_path, str)
        or "\\" in raw_path
        or any(ord(character) < 32 or ord(character) == 127 for character in raw_path)
    ):
        raise ProvenanceError(f"unsafe repository path: {raw_path!r}")
    path = PurePosixPath(raw_path)
    if not raw_path or path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ProvenanceError(f"unsafe repository path: {raw_path!r}")
    if raw_path != path.as_posix():
        raise ProvenanceError(f"repository path is not canonical POSIX syntax: {raw_path!r}")
    if ".git" in path.parts:
        raise ProvenanceError(f"repository metadata cannot be exported: {raw_path!r}")
    return path


def _git_mode(path: Path) -> str:
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode):
        raise ProvenanceError(f"symbolic links are not allowed in the export: {path}")
    if not stat.S_ISREG(info.st_mode):
        raise ProvenanceError(f"only regular files are allowed in the export: {path}")
    return "100755" if info.st_mode & stat.S_IXUSR else "100644"


def _file_record(root: Path, relative_path: PurePosixPath) -> dict[str, str]:
    path = root.joinpath(*relative_path.parts)
    content = path.read_bytes()
    return {
        "mode": _git_mode(path),
        "path": relative_path.as_posix(),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def collect_inventory(root: Path, *, include_source_manifest: bool = False) -> list[dict[str, str]]:
    """Collect the exact regular-file inventory for a rendered repository."""
    root = root.resolve()
    if not root.is_dir():
        raise ProvenanceError(f"export root is not a directory: {root}")

    paths: list[PurePosixPath] = []
    for directory, child_directories, filenames in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        retained_directories = []
        for child in sorted(child_directories):
            if child == ".git":
                if directory_path != root:
                    raise ProvenanceError(f"nested Git metadata is not allowed: {directory_path / child}")
                continue
            child_path = directory_path / child
            if child_path.is_symlink():
                raise ProvenanceError(f"symbolic links are not allowed in the export: {child_path}")
            retained_directories.append(child)
        child_directories[:] = retained_directories
        for filename in sorted(filenames):
            path = directory_path / filename
            if filename == ".git" and directory_path == root:
                continue
            relative = PurePosixPath(path.relative_to(root).as_posix())
            if not include_source_manifest and relative.as_posix() == SOURCE_MANIFEST:
                continue
            validate_relative_path(relative.as_posix())
            paths.append(relative)

    return [_file_record(root, path) for path in sorted(paths, key=lambda item: item.as_posix())]


def payload_sha256(files: Iterable[dict[str, str]]) -> str:
    """Hash the canonical path, mode, and content-hash inventory."""
    normalized = list(files)
    return hashlib.sha256(PAYLOAD_HASH_DOMAIN + canonical_json(normalized)).hexdigest()


def write_source_manifest(root: Path, manifest: dict[str, Any]) -> None:
    """Write SOURCE.json with stable field ordering and a final newline."""
    destination = root / SOURCE_MANIFEST
    destination.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    destination.chmod(0o644)


def _require_hex(value: Any, length: int, label: str) -> str:
    if not isinstance(value, str) or len(value) != length:
        raise ProvenanceError(f"{label} must be {length} lowercase hexadecimal characters")
    if any(character not in "0123456789abcdef" for character in value):
        raise ProvenanceError(f"{label} must be {length} lowercase hexadecimal characters")
    return value


def _expected_inventory(manifest: dict[str, Any]) -> list[dict[str, str]]:
    payload = manifest.get("payload")
    if not isinstance(payload, dict):
        raise ProvenanceError("SOURCE.json payload must be an object")
    files = payload.get("files")
    if not isinstance(files, list):
        raise ProvenanceError("SOURCE.json payload.files must be an array")

    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, record in enumerate(files):
        if not isinstance(record, dict) or set(record) != {"mode", "path", "sha256"}:
            raise ProvenanceError(f"SOURCE.json payload.files[{index}] has an invalid shape")
        path = validate_relative_path(record["path"]).as_posix()
        if path == SOURCE_MANIFEST:
            raise ProvenanceError("SOURCE.json cannot include itself in the payload")
        if path in seen:
            raise ProvenanceError(f"SOURCE.json contains a duplicate path: {path}")
        seen.add(path)
        mode = record["mode"]
        if mode not in {"100644", "100755"}:
            raise ProvenanceError(f"SOURCE.json has an unsupported mode for {path}: {mode}")
        normalized.append(
            {"mode": mode, "path": path, "sha256": _require_hex(record["sha256"], 64, f"{path} sha256")}
        )

    if normalized != sorted(normalized, key=lambda item: item["path"]):
        raise ProvenanceError("SOURCE.json payload.files must be sorted by path")
    return normalized


def verify_repository(root: Path) -> dict[str, Any]:
    """Verify the complete repository inventory and SOURCE.json hashes."""
    root = root.resolve()
    source_path = root / SOURCE_MANIFEST
    if not source_path.is_file():
        raise ProvenanceError(f"missing {SOURCE_MANIFEST}")
    try:
        source_text = source_path.read_text(encoding="utf-8")
        manifest = json.loads(source_text)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProvenanceError(f"invalid {SOURCE_MANIFEST}: {error}") from error
    if source_text != json.dumps(manifest, indent=2, sort_keys=True) + "\n":
        raise ProvenanceError(f"{SOURCE_MANIFEST} is not in canonical form")
    if _git_mode(source_path) != "100644":
        raise ProvenanceError(f"{SOURCE_MANIFEST} must have mode 100644")

    if not isinstance(manifest, dict) or set(manifest) != {
        "exporter",
        "payload",
        "schema_version",
        "source",
    }:
        raise ProvenanceError(f"{SOURCE_MANIFEST} has an invalid top-level shape")
    if type(manifest.get("schema_version")) is not int or manifest.get("schema_version") != SCHEMA_VERSION:
        raise ProvenanceError(f"{SOURCE_MANIFEST} schema_version must be {SCHEMA_VERSION}")
    source = manifest.get("source")
    if not isinstance(source, dict) or set(source) != {
        "commit",
        "repository",
        "subtree_git_tree",
        "subtree_path",
    }:
        raise ProvenanceError("SOURCE.json source has an invalid shape")
    if source.get("repository") != "Longshot-Labs/longshot":
        raise ProvenanceError("SOURCE.json source.repository is not the authoritative repository")
    if source.get("subtree_path") != "longshot-protocol":
        raise ProvenanceError("SOURCE.json source.subtree_path is not longshot-protocol")
    _require_hex(source.get("commit"), 40, "source commit")
    _require_hex(source.get("subtree_git_tree"), 40, "source subtree git tree")

    exporter = manifest.get("exporter")
    if not isinstance(exporter, dict) or set(exporter) != {"sha256"}:
        raise ProvenanceError("SOURCE.json exporter has an invalid shape")
    _require_hex(exporter.get("sha256"), 64, "exporter sha256")

    expected = _expected_inventory(manifest)
    actual = collect_inventory(root)
    if actual != expected:
        expected_by_path = {record["path"]: record for record in expected}
        actual_by_path = {record["path"]: record for record in actual}
        missing = sorted(set(expected_by_path) - set(actual_by_path))
        extra = sorted(set(actual_by_path) - set(expected_by_path))
        changed = sorted(
            path
            for path in set(expected_by_path) & set(actual_by_path)
            if expected_by_path[path] != actual_by_path[path]
        )
        details = []
        if missing:
            details.append(f"missing={','.join(missing)}")
        if extra:
            details.append(f"extra={','.join(extra)}")
        if changed:
            details.append(f"changed={','.join(changed)}")
        raise ProvenanceError("repository inventory differs from SOURCE.json: " + "; ".join(details))

    payload = manifest["payload"]
    if set(payload) != {"algorithm", "file_count", "files", "sha256"}:
        raise ProvenanceError("SOURCE.json payload has an invalid shape")
    if payload.get("algorithm") != "sha256":
        raise ProvenanceError("SOURCE.json payload.algorithm must be sha256")
    if type(payload.get("file_count")) is not int or payload.get("file_count") != len(actual):
        raise ProvenanceError("SOURCE.json payload.file_count does not match the inventory")
    expected_hash = _require_hex(payload.get("sha256"), 64, "payload sha256")
    actual_hash = payload_sha256(actual)
    if actual_hash != expected_hash:
        raise ProvenanceError(f"payload sha256 mismatch: expected {expected_hash}, got {actual_hash}")
    return manifest


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", type=Path, help="rendered repository root")
    arguments = parser.parse_args()
    try:
        manifest = verify_repository(arguments.root)
    except ProvenanceError as error:
        parser.error(str(error))
    print(
        "verified Longshot Protocol export "
        f"{manifest['payload']['sha256']} from {manifest['source']['commit']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
