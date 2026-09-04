#!/usr/bin/env python3
"""Fail closed unless this checkout is ready for an approved protocol release."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DOWNSTREAM_REPOSITORY = "Longshot-Labs/longshot-protocol"
UPSTREAM_REPOSITORY = "Longshot-Labs/longshot"
SYNC_BRANCH = "automation/sync-from-longshot-main"
RELEASE_ENVIRONMENT = "protocol-release"
DOWNSTREAM_CHECKS = {"provenance", "python", "rust", "typescript"}


class ReleaseGateError(RuntimeError):
    """A required release invariant is absent or unproven."""


def _require_environment(name: str, expected: str | None = None) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise ReleaseGateError(f"required environment value is not configured: {name}")
    if expected is not None and value != expected:
        raise ReleaseGateError(f"{name} must be {expected!r}, got {value!r}")
    return value


def _run(*command: str, cwd: Path | None = None) -> str:
    try:
        result = subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or error.stdout.strip()
        raise ReleaseGateError(f"command failed ({' '.join(command)}): {detail}") from error
    return result.stdout.strip()


def _api(token: str, repository: str, path: str, query: dict[str, str] | None = None) -> Any:
    suffix = f"?{urllib.parse.urlencode(query)}" if query else ""
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repository}/{path}{suffix}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "longshot-protocol-release-gate",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as error:
        status = getattr(error, "code", "network error")
        raise ReleaseGateError(f"GitHub setup check failed for {repository}/{path}: {status}") from error


def _app_bound_status_checks(protection: dict[str, Any]) -> dict[str, int]:
    required = protection.get("required_status_checks") or {}
    return {
        check["context"]: check["app_id"]
        for check in required.get("checks", [])
        if isinstance(check, dict)
        and isinstance(check.get("context"), str)
        and type(check.get("app_id")) is int
        and check["app_id"] > 0
    }


def _check_branch_protection(
    token: str,
    repository: str,
    required_checks: set[str],
) -> dict[str, int]:
    protection = _api(token, repository, "branches/main/protection")
    if not isinstance(protection, dict):
        raise ReleaseGateError(f"{repository} main branch protection response is invalid")
    reviews = protection.get("required_pull_request_reviews")
    if not isinstance(reviews, dict):
        raise ReleaseGateError(f"{repository} main must require pull request reviews")
    if int(reviews.get("required_approving_review_count", 0)) < 1:
        raise ReleaseGateError(f"{repository} main must require at least one approval")
    for setting in ("dismiss_stale_reviews", "require_code_owner_reviews", "require_last_push_approval"):
        if reviews.get(setting) is not True:
            raise ReleaseGateError(f"{repository} main protection must enable {setting}")
    bypass = reviews.get("bypass_pull_request_allowances") or {}
    if not isinstance(bypass, dict) or any(bypass.get(kind) for kind in ("apps", "teams", "users")):
        raise ReleaseGateError(f"{repository} main protection cannot allow pull request bypass actors")
    if (protection.get("enforce_admins") or {}).get("enabled") is not True:
        raise ReleaseGateError(f"{repository} main protection must include administrators")
    if (protection.get("allow_force_pushes") or {}).get("enabled") is True:
        raise ReleaseGateError(f"{repository} main protection must block force pushes")
    if (protection.get("allow_deletions") or {}).get("enabled") is True:
        raise ReleaseGateError(f"{repository} main protection must block deletion")
    required_status_checks = protection.get("required_status_checks") or {}
    if required_status_checks.get("strict") is not True:
        raise ReleaseGateError(f"{repository} main must require up-to-date status checks")
    bound_checks = _app_bound_status_checks(protection)
    missing = required_checks - set(bound_checks)
    if missing:
        raise ReleaseGateError(
            f"{repository} main protection is missing app-bound checks: {', '.join(sorted(missing))}"
        )
    return {name: bound_checks[name] for name in required_checks}


def _check_release_environment(token: str) -> None:
    environment = _api(token, DOWNSTREAM_REPOSITORY, f"environments/{RELEASE_ENVIRONMENT}")
    if not isinstance(environment, dict):
        raise ReleaseGateError("protocol-release environment response is invalid")
    if environment.get("can_admins_bypass") is not False:
        raise ReleaseGateError("protocol-release must disable administrator bypass")
    rules = environment.get("protection_rules")
    if not isinstance(rules, list):
        raise ReleaseGateError("protocol-release environment protection rules are invalid")
    review_rule = next(
        (
            rule
            for rule in rules or []
            if isinstance(rule, dict)
            and rule.get("type") == "required_reviewers"
            and bool(rule.get("reviewers"))
        ),
        None,
    )
    if review_rule is None:
        raise ReleaseGateError("protocol-release must require at least one human reviewer")
    if review_rule.get("prevent_self_review") is not True:
        raise ReleaseGateError("protocol-release must prevent self-review")
    branch_policy = environment.get("deployment_branch_policy")
    if (
        not isinstance(branch_policy, dict)
        or branch_policy.get("protected_branches") is not True
        or branch_policy.get("custom_branch_policies") is not False
    ):
        raise ReleaseGateError("protocol-release must allow protected branches only")


def _active_codeowner_patterns(root: Path) -> set[str]:
    path = root / ".github/CODEOWNERS"
    if not path.is_file():
        raise ReleaseGateError(f"missing CODEOWNERS in {root}")
    patterns = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        if len(fields) < 2 or not all(owner.startswith("@") for owner in fields[1:]):
            raise ReleaseGateError(f"invalid CODEOWNERS line: {raw_line}")
        patterns.add(fields[0])
    return patterns


def _require_codeowners(root: Path, patterns: set[str]) -> None:
    active = _active_codeowner_patterns(root)
    missing = patterns - active
    if missing:
        raise ReleaseGateError(
            f"{root / '.github/CODEOWNERS'} is missing required patterns: {', '.join(sorted(missing))}"
        )


def _check_commit_status(
    token: str,
    repository: str,
    commit: str,
    required_app_ids: dict[str, int],
) -> None:
    response = _api(token, repository, f"commits/{commit}/check-runs", {"per_page": "100"})
    runs = response.get("check_runs") if isinstance(response, dict) else None
    if not isinstance(runs, list):
        raise ReleaseGateError(f"could not read {repository} check runs")
    latest: dict[str, dict[str, Any]] = {}
    for run in runs:
        if (
            not isinstance(run, dict)
            or not isinstance(run.get("name"), str)
            or run.get("head_sha") != commit
            or (run.get("app") or {}).get("slug") != "github-actions"
        ):
            continue
        name = run["name"]
        app = run.get("app") or {}
        if (
            name in required_app_ids
            and app.get("id") == required_app_ids[name]
            and int(run.get("id", 0)) > int(latest.get(name, {}).get("id", 0))
        ):
            latest[name] = run
    missing = set(required_app_ids) - set(latest)
    if missing:
        raise ReleaseGateError(f"{repository} commit is missing CI checks: {', '.join(sorted(missing))}")
    failed = sorted(
        name
        for name, run in latest.items()
        if run.get("status") != "completed" or run.get("conclusion") != "success"
    )
    if failed:
        raise ReleaseGateError(f"{repository} commit has non-success CI checks: {', '.join(failed)}")


def _check_no_pending_sync(token: str) -> None:
    pulls = _api(
        token,
        DOWNSTREAM_REPOSITORY,
        "pulls",
        {"head": f"Longshot-Labs:{SYNC_BRANCH}", "per_page": "1", "state": "open"},
    )
    if not isinstance(pulls, list):
        raise ReleaseGateError("could not read downstream pull requests")
    if pulls:
        raise ReleaseGateError(f"release blocked by open protocol sync PR #{pulls[0].get('number', '?')}")


def _check_main_head(token: str, repository: str, expected_commit: str) -> None:
    reference = _api(token, repository, "git/ref/heads/main")
    commit = reference.get("object", {}).get("sha") if isinstance(reference, dict) else None
    if commit != expected_commit:
        raise ReleaseGateError(f"{repository} main moved during release verification")


def _check_codeowner_errors(token: str, repository: str) -> None:
    response = _api(token, repository, "codeowners/errors")
    errors = response.get("errors") if isinstance(response, dict) else None
    if not isinstance(errors, list):
        raise ReleaseGateError(f"{repository} CODEOWNERS error response is invalid")
    if errors:
        raise ReleaseGateError(f"{repository} CODEOWNERS contains invalid patterns or owners")


def _manifest(root: Path) -> dict[str, Any]:
    path = root / "SOURCE.json"
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseGateError(f"invalid {path}: {error}") from error
    if not isinstance(result, dict):
        raise ReleaseGateError(f"invalid {path}: root must be an object")
    return result


def _version(root: Path) -> str:
    rust = (root / "rust/Cargo.toml").read_text(encoding="utf-8")
    python = (root / "python/pyproject.toml").read_text(encoding="utf-8")
    typescript = json.loads((root / "typescript/package.json").read_text(encoding="utf-8"))
    rust_match = re.search(r"(?m)^version = \"([^\"]+)\"$", rust)
    python_match = re.search(r"(?m)^version = \"([^\"]+)\"$", python)
    versions = {
        rust_match.group(1) if rust_match else "",
        python_match.group(1) if python_match else "",
        typescript.get("longshotReleaseVersion", "") if isinstance(typescript, dict) else "",
    }
    if "" in versions or len(versions) != 1:
        raise ReleaseGateError("Rust, Python, and TypeScript versions must be present and equal")
    return versions.pop()


def check_release(
    root: Path,
    upstream_root: Path,
    recorded_export: Path,
    latest_export: Path,
    token: str,
) -> None:
    root = root.resolve()
    upstream_root = upstream_root.resolve()
    recorded_export = recorded_export.resolve()
    latest_export = latest_export.resolve()
    _require_environment("GITHUB_ACTIONS", "true")
    _require_environment("GITHUB_EVENT_NAME", "workflow_dispatch")
    _require_environment("GITHUB_REPOSITORY", DOWNSTREAM_REPOSITORY)
    _require_environment("GITHUB_REF", "refs/heads/main")
    commit = _require_environment("GITHUB_SHA")
    _require_environment("PROTOCOL_RELEASE_ENABLED", "true")
    _require_environment("PROTOCOL_RELEASE_ENVIRONMENT_CONFIGURED", "v1")

    if _run("git", "rev-parse", "HEAD", cwd=root) != commit:
        raise ReleaseGateError("release checkout does not match GITHUB_SHA")
    if _run("git", "status", "--porcelain", "--untracked-files=all", cwd=root):
        raise ReleaseGateError("release checkout is not clean")
    _run(sys.executable, str(root / "scripts/check-source-provenance.py"), str(root))
    _run(sys.executable, str(recorded_export / "scripts/check-source-provenance.py"), str(recorded_export))
    _run(sys.executable, str(latest_export / "scripts/check-source-provenance.py"), str(latest_export))
    current_manifest = _manifest(root)
    recorded_manifest = _manifest(recorded_export)
    latest_manifest = _manifest(latest_export)
    expected_source = _require_environment("EXPECTED_SOURCE_SHA")
    if current_manifest.get("source", {}).get("commit") != expected_source:
        raise ReleaseGateError("EXPECTED_SOURCE_SHA does not match SOURCE.json")
    if current_manifest != recorded_manifest:
        raise ReleaseGateError("downstream main does not match a replay of its recorded upstream source")
    latest_upstream_commit = _run("git", "rev-parse", "HEAD", cwd=upstream_root)
    if latest_manifest.get("source", {}).get("commit") != latest_upstream_commit:
        raise ReleaseGateError("latest export does not identify the checked-out upstream main commit")
    try:
        _run("git", "merge-base", "--is-ancestor", expected_source, latest_upstream_commit, cwd=upstream_root)
    except ReleaseGateError as error:
        raise ReleaseGateError("recorded upstream source is not an ancestor of current upstream main") from error
    if current_manifest.get("payload") != latest_manifest.get("payload"):
        raise ReleaseGateError("downstream main payload differs from the latest upstream export")
    expected_version = _require_environment("EXPECTED_VERSION")
    actual_version = _version(root)
    if actual_version != expected_version:
        raise ReleaseGateError(f"expected version {expected_version}, found {actual_version}")

    _require_codeowners(
        root,
        {"/.github/CODEOWNERS", "/.github/workflows/", "/SOURCE.json", "/scripts/"},
    )
    _require_codeowners(
        upstream_root,
        {
            "/.github/CODEOWNERS",
            "/.github/workflows/",
            "/longshot-protocol/",
            "/scripts/protocol_sync/",
        },
    )
    _check_codeowner_errors(token, DOWNSTREAM_REPOSITORY)
    _check_codeowner_errors(token, UPSTREAM_REPOSITORY)
    downstream_check_apps = _check_branch_protection(token, DOWNSTREAM_REPOSITORY, DOWNSTREAM_CHECKS)
    upstream_check_apps = _check_branch_protection(token, UPSTREAM_REPOSITORY, {"Protocol Export"})
    _check_release_environment(token)
    _check_main_head(token, DOWNSTREAM_REPOSITORY, commit)
    _check_main_head(token, UPSTREAM_REPOSITORY, latest_upstream_commit)
    _check_commit_status(token, DOWNSTREAM_REPOSITORY, commit, downstream_check_apps)
    _check_commit_status(token, UPSTREAM_REPOSITORY, latest_upstream_commit, upstream_check_apps)
    _check_no_pending_sync(token)


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--upstream-root", type=Path, required=True)
    parser.add_argument("--recorded-export", type=Path, required=True)
    parser.add_argument("--latest-export", type=Path, required=True)
    arguments = parser.parse_args()
    token = os.environ.get("LONGSHOT_PROTOCOL_SETTINGS_READ_TOKEN", "")
    if not token:
        parser.error("LONGSHOT_PROTOCOL_SETTINGS_READ_TOKEN is not configured")
    try:
        check_release(
            arguments.root,
            arguments.upstream_root,
            arguments.recorded_export,
            arguments.latest_export,
            token,
        )
    except ReleaseGateError as error:
        parser.error(str(error))
    print("release gate passed; no package was published")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
