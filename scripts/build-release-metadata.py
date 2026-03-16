#!/usr/bin/env python3
import datetime as dt
import gzip
import hashlib
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "public" / "debian" / "dists" / "trixie"
BINARY = DIST / "main" / "binary-amd64"
POOL = ROOT / "public" / "debian" / "pool" / "main"
PACKAGES = BINARY / "Packages"
PACKAGES_GZ = BINARY / "Packages.gz"
RELEASE = DIST / "Release"


def digest(path: Path, name: str) -> str:
    h = hashlib.new(name)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_packages() -> None:
    BINARY.mkdir(parents=True, exist_ok=True)
    POOL.mkdir(parents=True, exist_ok=True)

    debs = sorted(POOL.rglob("*.deb"))
    dpkg_scanpackages = shutil.which("dpkg-scanpackages")

    if debs and not dpkg_scanpackages:
        raise SystemExit("found .deb files in pool/ but dpkg-scanpackages is not available")

    if dpkg_scanpackages:
        proc = subprocess.run(
            [dpkg_scanpackages, str(POOL), "/dev/null"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        content = proc.stdout
    else:
        content = ""

    PACKAGES.write_text(content, encoding="utf-8")
    with PACKAGES_GZ.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
            gz.write(content.encode("utf-8"))


def write_release() -> None:
    files = [
        (PACKAGES.relative_to(DIST), PACKAGES),
        (PACKAGES_GZ.relative_to(DIST), PACKAGES_GZ),
    ]

    lines = [
        "Origin: Riff Labs",
        "Label: Riff Labs",
        "Suite: trixie",
        "Codename: trixie",
        "Architectures: amd64",
        "Components: main",
        f"Date: {dt.datetime.now(dt.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S %Z')}",
        "Description: Riff Labs Debian repository",
        "MD5Sum:",
    ]

    for rel, path in files:
        lines.append(f" {digest(path, 'md5')} {path.stat().st_size} {rel}")

    lines.append("SHA256:")
    for rel, path in files:
        lines.append(f" {digest(path, 'sha256')} {path.stat().st_size} {rel}")

    RELEASE.write_text("\n".join(lines) + "\n", encoding="utf-8")


RELEASE_GPG = DIST / "Release.gpg"
INRELEASE = DIST / "InRelease"


def sign_release() -> None:
    gpg_key = os.environ.get("GPG_SIGNING_KEY")
    if not gpg_key:
        print("GPG_SIGNING_KEY not set, skipping signing")
        return

    subprocess.run(
        ["gpg", "--batch", "--import"],
        input=gpg_key,
        text=True,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    key_id = os.environ.get("GPG_KEY_ID", "")
    key_args = ["--default-key", key_id] if key_id else []

    subprocess.run(
        ["gpg", "--batch", "--yes", "--armor", "--detach-sign", *key_args,
         "--output", str(RELEASE_GPG), str(RELEASE)],
        check=True,
    )

    subprocess.run(
        ["gpg", "--batch", "--yes", "--armor", "--clearsign", *key_args,
         "--output", str(INRELEASE), str(RELEASE)],
        check=True,
    )

    print(f"Signed: {RELEASE_GPG.name}, {INRELEASE.name}")


def main() -> None:
    write_packages()
    write_release()
    sign_release()


if __name__ == "__main__":
    main()
