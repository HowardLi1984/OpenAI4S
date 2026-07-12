#!/usr/bin/env python3
"""Regenerate the Community Contributors avatar wall in the READMEs.

Fetches the repository's contributors straight from the GitHub API (the same
source as the sidebar / contributors graph) and rewrites the block between the
``CONTRIBUTORS`` markers in each README.  Unlike a third-party image service
(e.g. contrib.rocks, which anonymously rate-limits against the GitHub API and
was rendering only a single avatar for this repo), this runs in CI with the
repo's own token and always sees every attributed contributor.

Run in CI via ``.github/workflows/contributors.yml``; runnable locally for a
preview with ``GITHUB_TOKEN`` set or a ``gh auth`` session.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.request

REPO = os.environ.get("GITHUB_REPOSITORY", "PKU-YuanGroup/OpenAI4S")
READMES = ("README.md", "README_zh.md")
START = "<!-- CONTRIBUTORS:START -->"
END = "<!-- CONTRIBUTORS:END -->"
# Bots and the automated co-author identity never count as community members.
EXCLUDE = {"github-actions[bot]", "dependabot[bot]", "actions-user"}


def _token() -> str | None:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token
    try:  # local convenience only
        out = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=10
        )
        return out.stdout.strip() or None
    except Exception:  # noqa: BLE001
        return None


def fetch_contributors() -> list[dict]:
    token = _token()
    people: list[dict] = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/repos/{REPO}/contributors"
            f"?per_page=100&page={page}"
        )
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "openai4s-contributors-script",
            },
        )
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            batch = json.load(resp)
        if not batch:
            break
        people.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    seen: set[str] = set()
    kept: list[dict] = []
    for c in people:
        login = c.get("login")
        if c.get("type") != "User" or not login or login in EXCLUDE or login in seen:
            continue
        seen.add(login)
        kept.append(c)
    kept.sort(key=lambda c: c.get("contributions", 0), reverse=True)
    return kept


def render(people: list[dict]) -> str:
    return "\n".join(
        f'<a href="https://github.com/{c["login"]}">'
        f'<img src="https://github.com/{c["login"]}.png" '
        f'width="64" height="64" alt="{c["login"]}" /></a>'
        for c in people
    )


def update_file(path: str, block: str) -> bool:
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if START not in text or END not in text:
        print(f"markers not found in {path}", file=sys.stderr)
        return False
    replacement = f"{START}\n{block}\n{END}"
    updated = re.sub(
        re.escape(START) + r".*?" + re.escape(END),
        lambda _m: replacement,
        text,
        flags=re.DOTALL,
    )
    if updated == text:
        return False
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(updated)
    return True


def main() -> int:
    people = fetch_contributors()
    if not people:
        print("no contributors fetched (rate limit or auth?)", file=sys.stderr)
        return 1
    block = render(people)
    changed = [p for p in READMES if os.path.exists(p) and update_file(p, block)]
    print(
        f"{len(people)} contributors: "
        + ", ".join(c["login"] for c in people)
        + f"\nupdated: {changed or 'nothing (already current)'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
