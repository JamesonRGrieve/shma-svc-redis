"""Validate Redis ACL files without requiring a Redis server.

The script checks the basic ACL grammar so CI hosts do not need to run
`redis-server` or `redis-cli`. It exits with code 0 when the ACL file is valid
and with a non-zero code otherwise.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import shlex
import sys
from typing import Iterable

ALLOWED_KEYWORDS = {
    "on",
    "off",
    "nopass",
    "resetpass",
    "resetkeys",
    "resetchannels",
    "resetcommands",
    "allcommands",
    "allkeys",
    "allchannels",
}

COMMAND_RE = re.compile(r"^[+-](?:@?[A-Za-z0-9_:\-]+|\*)$")
CATEGORY_RE = re.compile(r"^[+-]@(?:[A-Za-z0-9_:\-]+|all)$")
KEY_RE = re.compile(r"^[~&%].+")
PASSWORD_RE = re.compile(r"^[><].+")
HASH_RE = re.compile(r"^#[0-9a-fA-F]{40,128}$")


class ACLValidationError(Exception):
    """Raised when the ACL grammar is invalid."""


def iter_acl_lines(content: str) -> Iterable[tuple[int, list[str]]]:
    """Yield (line_number, tokens) pairs for non-empty ACL lines."""

    for idx, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            tokens = shlex.split(line)
        except ValueError as exc:  # unmatched quotes, etc.
            raise ACLValidationError(f"Line {idx}: {exc}") from exc
        yield idx, tokens


def validate_acl_tokens(line_number: int, tokens: list[str]) -> None:
    """Ensure the provided token list represents a valid ACL rule."""

    if not tokens:
        raise ACLValidationError(f"Line {line_number}: empty ACL rule")
    if tokens[0] != "user":
        raise ACLValidationError(
            f"Line {line_number}: ACL rules must start with the 'user' keyword"
        )
    if len(tokens) == 1:
        raise ACLValidationError(
            f"Line {line_number}: missing user name after the 'user' keyword"
        )

    username = tokens[1]
    if username in {"", "default"} and len(tokens) == 2:
        raise ACLValidationError(
            f"Line {line_number}: user '{username}' must include at least one rule"
        )

    for token in tokens[2:]:
        if token in ALLOWED_KEYWORDS:
            continue
        if COMMAND_RE.match(token):
            continue
        if CATEGORY_RE.match(token):
            continue
        if KEY_RE.match(token):
            continue
        if PASSWORD_RE.match(token):
            continue
        if HASH_RE.match(token):
            continue
        raise ACLValidationError(
            f"Line {line_number}: unsupported token '{token}' in ACL rule"
        )


def validate_acl_file(path: pathlib.Path) -> None:
    content = path.read_text(encoding="utf-8")
    has_user = False
    for line_number, tokens in iter_acl_lines(content):
        validate_acl_tokens(line_number, tokens)
        has_user = True
    if not has_user:
        raise ACLValidationError("ACL file is empty")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("acl_file", type=pathlib.Path, help="Path to the ACL file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        validate_acl_file(args.acl_file)
    except ACLValidationError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
