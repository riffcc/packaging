#!/usr/bin/env python3
"""Fetch .deb artifacts from GitHub releases for all released packages."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"
POOL = ROOT / "public" / "debian" / "pool" / "main"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def released_repos(catalog: dict) -> set[str]:
    repos: set[str] = set()
    for pkg in catalog.get("packages", []):
        if pkg.get("status") == "released" and pkg.get("repo"):
            repos.add(pkg["repo"])
    return repos


def fetch_debs_from_repo(repo: str) -> None:
    result = subprocess.run(
        ["gh", "release", "view", "--repo", repo, "--json", "assets"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  No release found for {repo}, skipping")
        return

    assets = json.loads(result.stdout).get("assets", [])
    deb_assets = [a for a in assets if a["name"].endswith(".deb")]

    if not deb_assets:
        print(f"  No .deb assets in latest release for {repo}")
        return

    for asset in deb_assets:
        dest = POOL / asset["name"]
        if dest.exists():
            print(f"  {asset['name']} already present, skipping")
            continue
        print(f"  Downloading {asset['name']}")
        subprocess.run(
            ["gh", "release", "download", "--repo", repo,
             "--pattern", asset["name"], "--dir", str(POOL)],
            check=True,
        )


def main() -> None:
    POOL.mkdir(parents=True, exist_ok=True)

    repos: set[str] = set()
    for catalog_file in CONFIG.glob("*-packages.json"):
        catalog = load_json(catalog_file)
        repos |= released_repos(catalog)

    if not repos:
        print("No released repos found")
        return

    for repo in sorted(repos):
        print(f"Fetching from {repo}")
        fetch_debs_from_repo(repo)

    debs = list(POOL.glob("*.deb"))
    print(f"\nPool contains {len(debs)} .deb file(s)")


if __name__ == "__main__":
    main()
