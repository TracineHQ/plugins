#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 TracineHQ contributors
"""Sync plugin ``version`` fields in marketplace.json to each source repo's latest release tag.

For every entry in ``plugins[]``, derive the GitHub ``owner/repo`` from the
``source.url`` (preferred) or ``homepage`` field, query the GitHub REST API
for the latest published release, strip the leading ``v`` if present, and
write back if the manifest's recorded ``version`` differs.

Stdlib-only by design -- this is operational tooling, not application code,
and pulling a third-party HTTP client in just for two endpoints would be
deadweight surface area. Reads ``GITHUB_TOKEN`` from the env to authenticate
(avoids the 60-req/hour unauthenticated rate limit). Exits non-zero only on
network or schema errors; "no drift" is a successful no-op.

Usage:
    python3 scripts/sync_marketplace_versions.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"
GITHUB_REPO_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[A-Za-z0-9._-]+)/(?P<repo>[A-Za-z0-9._-]+?)(?:\.git)?/?$"
)
# Reject release tags that contain whitespace, control chars, or shell/JSON
# metacharacters. A compromised upstream repo could otherwise inject odd
# strings into marketplace.json's version field. ~64-char ceiling matches
# Git's reasonable tag length; longer tags are almost certainly noise.
_VALID_TAG_RE = re.compile(r"^[0-9A-Za-z][0-9A-Za-z.+_-]{0,63}$")
USER_AGENT = "tracinehq-marketplace-sync/1.0"


class SyncError(RuntimeError):
    """Operator-visible failure. Printed; non-zero exit."""


def _derive_repo(plugin: dict[str, Any]) -> str | None:
    """Return ``owner/repo`` from a plugin entry's source.url or homepage."""
    source = plugin.get("source")
    if isinstance(source, dict):
        url = source.get("url")
        if isinstance(url, str):
            m = GITHUB_REPO_RE.match(url)
            if m:
                return f"{m.group('owner')}/{m.group('repo')}"
    homepage = plugin.get("homepage")
    if isinstance(homepage, str):
        m = GITHUB_REPO_RE.match(homepage)
        if m:
            return f"{m.group('owner')}/{m.group('repo')}"
    return None


def _fetch_latest_release_tag(owner_repo: str, *, token: str | None) -> str | None:
    """Return the latest release tag for ``owner_repo`` (e.g. ``"v1.4.1"``), or None.

    Uses the ``/releases/latest`` endpoint which excludes prereleases and
    drafts. Returns None for repos with zero published releases (200 missing,
    or 404 from GitHub). Raises SyncError on transport / auth / schema errors
    so a misconfigured run fails loudly rather than silently no-op.
    """
    url = f"https://api.github.com/repos/{owner_repo}/releases/latest"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)  # noqa: S310 -- https URL fixed at module load
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 -- see above
            body = resp.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        msg = f"GitHub API error for {owner_repo}: HTTP {e.code} {e.reason}"
        raise SyncError(msg) from e
    except urllib.error.URLError as e:
        msg = f"Network error fetching releases for {owner_repo}: {e.reason}"
        raise SyncError(msg) from e
    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        msg = f"Malformed JSON from GitHub for {owner_repo}: {e}"
        raise SyncError(msg) from e
    tag = data.get("tag_name") if isinstance(data, dict) else None
    if not isinstance(tag, str) or not _VALID_TAG_RE.match(tag):
        return None
    return tag


def _normalize_tag(tag: str) -> str:
    """Strip a leading ``v`` so ``v1.4.1`` and ``1.4.1`` compare equal."""
    return tag[1:] if tag.startswith("v") else tag


def sync(*, dry_run: bool) -> int:
    """Drive the sync. Returns 0 if no drift, 1 if changes written (or would be)."""
    if not MARKETPLACE.exists():
        msg = f"marketplace manifest not found at {MARKETPLACE}"
        raise SyncError(msg)
    raw_text = MARKETPLACE.read_text(encoding="utf-8")
    try:
        manifest = json.loads(raw_text)
    except json.JSONDecodeError as e:
        msg = f"marketplace.json is not valid JSON: {e}"
        raise SyncError(msg) from e
    plugins = manifest.get("plugins")
    if not isinstance(plugins, list):
        msg = "marketplace.json: 'plugins' must be an array"
        raise SyncError(msg)

    token = os.environ.get("GITHUB_TOKEN") or None
    changed = False
    for plugin in plugins:
        if not isinstance(plugin, dict):
            continue
        name = plugin.get("name", "<unknown>")
        owner_repo = _derive_repo(plugin)
        if owner_repo is None:
            print(f"skip: {name}: no GitHub URL derivable from source/homepage", file=sys.stderr)
            continue
        # Per-plugin network errors degrade to skip so one flaky upstream
        # doesn't block every other plugin's sync for the day.
        try:
            latest = _fetch_latest_release_tag(owner_repo, token=token)
        except SyncError as e:
            print(f"skip: {name}: {e}", file=sys.stderr)
            continue
        if latest is None:
            print(f"skip: {name}: {owner_repo} has no published release yet", file=sys.stderr)
            continue
        new_version = _normalize_tag(latest)
        current = plugin.get("version")
        if current == new_version:
            print(f"ok:   {name}: already at {current}")
            continue
        print(f"bump: {name}: {current!r} -> {new_version!r}")
        plugin["version"] = new_version
        changed = True

    if not changed:
        print("no drift; marketplace.json unchanged")
        return 0

    if dry_run:
        print("--dry-run: not writing")
        return 1

    MARKETPLACE.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {MARKETPLACE.relative_to(REPO_ROOT)}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report drift without writing; exit 1 if drift exists.",
    )
    args = parser.parse_args()
    try:
        return sync(dry_run=args.dry_run)
    except SyncError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
