#!/usr/bin/env python3
"""Reject credential-shaped values from extracted public package archives."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


PATTERNS = {
    "PEM private key": re.compile(
        r"-----BEGIN ((?:[A-Z0-9][A-Z0-9 -]* )?PRIVATE KEY)-----\s+"
        r"[A-Za-z0-9+/=\r\n]{32,}\s+-----END \1-----"
    ),
    "JWT": re.compile(
        r"(?<![A-Za-z0-9_-])eyJ[A-Za-z0-9_-]{8,}\."
        r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}(?![A-Za-z0-9_-])"
    ),
    "AWS access key": re.compile(
        r"(?<![A-Z0-9])(?:AKIA|ASIA|AIDA|AROA|AIPA|ANPA|ANVA|ASCA)"
        r"[A-Z0-9]{16}(?![A-Z0-9])"
    ),
    "prefixed access token": re.compile(
        r"(?<![A-Za-z0-9])(?:"
        r"gh[pousr]_[A-Za-z0-9]{30,}|"
        r"github_pat_[A-Za-z0-9_]{40,}|"
        r"glpat-[A-Za-z0-9_-]{20,}|"
        r"xox[baprs]-[A-Za-z0-9-]{20,}|"
        r"sk_live_[A-Za-z0-9]{20,}|"
        r"npm_[A-Za-z0-9]{36,}|"
        r"pypi-[A-Za-z0-9_-]{40,}"
        r")(?![A-Za-z0-9])"
    ),
    "AWS secret access key": re.compile(
        r"(?im)\bAWS_SECRET_ACCESS_KEY\b\s*[:=]\s*[\"']?"
        r"[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])"
    ),
    "hex private key": re.compile(
        r"(?im)\b(?:EVM_)?PRIVATE_KEY\b\s*[:=]\s*[\"']?"
        r"0x[0-9a-f]{64}(?![0-9a-f])"
    ),
    "bearer token": re.compile(
        r"(?i)\bAuthorization\s*:\s*Bearer\s+"
        r"[A-Za-z0-9._~+/=-]{20,}(?![A-Za-z0-9._~+/=-])"
    ),
    "Basic credentials": re.compile(
        r"(?i)\bAuthorization\s*:\s*Basic\s+"
        r"[A-Za-z0-9+/]{16,}={0,2}(?![A-Za-z0-9+/=])"
    ),
    "credential assignment": re.compile(
        r"(?im)\b(?:[A-Z0-9]+_)*(?:API_KEY|ACCESS_TOKEN|AUTH_TOKEN|"
        r"APP_SECRET|API_SECRET|CLIENT_SECRET|CLIENT_TOKEN|KEY_SECRET|"
        r"PRIVATE_KEY|SECRET_KEY|SESSION_TOKEN|SIGNING_KEY|WEBHOOK_SECRET|PASSWORD)\b"
        r"\s*[:=]\s*[\"']?(?![<${])"
        r"[A-Za-z0-9._~+/=-]{24,}(?![A-Za-z0-9._~+/=-])"
    ),
}
CREDENTIAL_URL = re.compile(
    r"\b(?:https?|postgres(?:ql)?|mysql|redis|amqps?|mongodb(?:\+srv)?)://"
    r"(?P<user>[^\s/:@{}<>$]+):(?P<password>[^\s/@{}<>$]+)@"
    r"(?P<host>[^\s/]+)",
    re.IGNORECASE,
)
PLACEHOLDER_PASSWORDS = {
    "example",
    "pass",
    "password",
    "secret",
    "token",
    "user",
    "username",
}
PLACEHOLDER_HOSTS = {"127.0.0.1", "localhost"}


def is_placeholder_host(raw_host: str) -> bool:
    host = raw_host.lower().split(":", maxsplit=1)[0].rstrip(".")
    return host in PLACEHOLDER_HOSTS or host.endswith(
        (".example", ".invalid", ".localhost", ".test")
    )


def findings(text: str) -> set[str]:
    result = {name for name, pattern in PATTERNS.items() if pattern.search(text)}
    for match in CREDENTIAL_URL.finditer(text):
        placeholder_password = match.group("password").lower() in PLACEHOLDER_PASSWORDS
        if not placeholder_password or not is_placeholder_host(match.group("host")):
            result.add("credential-bearing URL")
    return result


def scan(roots: list[Path]) -> int:
    failed = False
    for root in roots:
        if root.is_file():
            paths = [root]
        elif root.is_dir():
            paths = root.rglob("*")
        else:
            raise SystemExit(f"archive secret scan root does not exist: {root}")
        for path in paths:
            if not path.is_file():
                continue
            text = path.read_bytes().decode("utf-8", errors="ignore")
            for kind in sorted(findings(text)):
                print(f"public package contains {kind}: {path}")
                failed = True
    return int(failed)


def self_test() -> int:
    probes = {
        "PEM private key": (
            "-----BEGIN PRIVATE KEY-----\n"
            "QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVo0123456789\n"
            "-----END PRIVATE KEY-----"
        ),
        "JWT": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.c2lnbmF0dXJlX3ZhbHVl",
        "AWS access key": "AKIAIOSFODNN7EXAMPLE",
        "prefixed access token": "ghp_0123456789abcdefghijklmnopqrstuvwxyzAB",
        "AWS secret access key": "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "hex private key": "PRIVATE_KEY=0x" + "0123456789abcdef" * 4,
        "bearer token": "Authorization: Bearer live-token-0123456789abcdef",
        "Basic credentials": "Authorization: Basic dXNlcjpyZWFsLWNsaWVudC1zZWNyZXQ=",
        "credential assignment": "LONGSHOT_API_KEY=0123456789abcdefghijklmnopqrstuv",
        "credential-bearing URL": "postgresql://user:real-credential@db.invalid/main",
    }
    for expected, probe in probes.items():
        if expected not in findings(probe):
            print(f"archive secret self-test did not reject {expected}")
            return 1
    for assignment in (
        "PRIVY_APP_SECRET=0123456789abcdefghijklmnopqrstuv",
        "EVM_PRIVATE_KEY=" + "0123456789abcdef" * 4,
        "DATABASE_PASSWORD=0123456789abcdefghijklmnopqrstuv",
    ):
        if "credential assignment" not in findings(assignment):
            print("archive secret self-test allowed a credential assignment")
            return 1
    for expected, probe in {
        "JWT": probes["JWT"] + "...",
        "AWS access key": probes["AWS access key"] + "...",
        "prefixed access token": probes["prefixed access token"] + "...",
        "credential-bearing URL": "postgresql://prod:ActualSecret...@db.invalid/main",
    }.items():
        if expected not in findings(probe):
            print(f"archive secret self-test allowed {expected} before ellipsis")
            return 1
    safe = (
        "Authorization: Bearer <TOKEN>\n"
        "Authorization: Basic <BASE64_CREDENTIALS>\n"
        "AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}\n"
        "CLIENT_SECRET=<CLIENT_SECRET>\n"
        "LONGSHOT_API_KEY=${LONGSHOT_API_KEY}\n"
        "SIGNING_KEY=<64_HEX_DIGITS>\n"
        "PRIVATE_KEY=<0x-private-key>\n"
        "postgresql://user:password@db.invalid/main\n"
    )
    if detected := findings(safe):
        print(f"archive secret self-test rejected placeholders: {sorted(detected)}")
        return 1
    for production_url in (
        "postgresql://prod:secret@production-db.longshot.xyz/main",
        "redis://admin:password@cache.longshot.xyz/0",
        "https://service:token@api.longshot.xyz/v1",
    ):
        if "credential-bearing URL" not in findings(production_url):
            print("archive secret self-test allowed credentials on a production host")
            return 1
    print("Archive secret scan self-tests passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("roots", nargs="*", type=Path)
    args = parser.parse_args()
    if args.self_test:
        if args.roots:
            parser.error("--self-test does not accept archive roots")
        return self_test()
    if not args.roots:
        parser.error("provide one or more extracted archive roots")
    return scan(args.roots)


if __name__ == "__main__":
    raise SystemExit(main())
