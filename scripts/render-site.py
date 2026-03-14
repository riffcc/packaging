#!/usr/bin/env python3
import json
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
CONFIG = ROOT / "config"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_catalog(data: dict, *, require_repo: bool) -> None:
    if data.get("schema") != 1:
        raise SystemExit(f"{data}: unsupported schema")
    names = set()
    for package in data.get("packages", []):
        name = package.get("name")
        if not name:
            raise SystemExit("package is missing name")
        if name in names:
            raise SystemExit(f"duplicate package name: {name}")
        names.add(name)
        if require_repo and not package.get("repo"):
            raise SystemExit(f"public package {name} is missing repo")
        if not package.get("project"):
            raise SystemExit(f"package {name} is missing project")
        if not package.get("status"):
            raise SystemExit(f"package {name} is missing status")


def package_list_items(packages: list[dict]) -> str:
    rows = []
    for pkg in packages:
        repo = pkg.get("repo")
        repo_html = f"<p><strong>Repo:</strong> <code>{escape(repo)}</code></p>" if repo else ""
        rows.append(
            "".join(
                [
                    '<article class="package-card">',
                    f"<h3><code>{escape(pkg['name'])}</code></h3>",
                    f"<p><strong>Project:</strong> {escape(pkg['project'])}</p>",
                    repo_html,
                    f"<p><strong>Status:</strong> {escape(pkg['status'])}</p>",
                    '</article>',
                ]
            )
        )
    return "\n".join(rows)


def render_index(public_catalog: dict, allowlisted_catalog: dict) -> str:
    public_arches = ", ".join(public_catalog.get("architectures", []))
    dist = public_catalog.get("distribution", "trixie")
    public_cards = package_list_items(public_catalog.get("packages", []))
    private_cards = package_list_items(allowlisted_catalog.get("packages", []))
    return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>repos.riff.cc</title>
    <link rel=\"stylesheet\" href=\"/styles.css\">
  </head>
  <body>
    <main class=\"shell\">
      <section class=\"hero\">
        <p class=\"eyebrow\">Riff Labs Packaging</p>
        <h1>repos.riff.cc</h1>
        <p class=\"lede\">Public packages, Debian metadata, and install guides for the Riff Labs stack. This site is rendered from package catalog metadata in the packaging repo.</p>
      </section>

      <section class=\"panel\">
        <h2>Public Debian Repository</h2>
        <p>Current distribution target: Debian 13 <code>{escape(public_arches)}</code>.</p>
        <pre><code>deb [arch={escape(public_arches)}] https://repos.riff.cc/debian {escape(dist)} main</code></pre>
      </section>

      <section class=\"panel\">
        <h2>Public Package Catalog</h2>
        <div class=\"packages\">
          {public_cards}
        </div>
      </section>

      <section class=\"panel\">
        <h2>Allowlisted Package Families</h2>
        <p>{escape(allowlisted_catalog['policy']['note'])}</p>
        <div class=\"packages\">
          {private_cards}
        </div>
      </section>

      <section class=\"panel\">
        <h2>Machine-readable Metadata</h2>
        <ul>
          <li><a href=\"/catalog.json\">catalog.json</a></li>
          <li><a href=\"/debian/dists/{escape(dist)}/main/binary-amd64/Packages\">Packages</a></li>
          <li><a href=\"/debian/dists/{escape(dist)}/Release\">Release</a></li>
        </ul>
      </section>
    </main>
  </body>
</html>
"""


def main() -> None:
    public_catalog = load_json(CONFIG / "public-packages.json")
    allowlisted_catalog = load_json(CONFIG / "allowlisted-packages.json")
    validate_catalog(public_catalog, require_repo=True)
    validate_catalog(allowlisted_catalog, require_repo=False)

    merged = {
        "schema": 1,
        "channels": {
            "public": public_catalog,
            "allowlisted": allowlisted_catalog,
        },
    }
    (PUBLIC / "catalog.json").write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    (PUBLIC / "index.html").write_text(render_index(public_catalog, allowlisted_catalog), encoding="utf-8")


if __name__ == "__main__":
    main()
