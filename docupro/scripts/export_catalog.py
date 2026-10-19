"""Export the conversion catalog as a stable contract file.

The web client, the desktop shell and the mobile shell all consume the same
catalog. Committing the exported JSON lets the front-end contract be reviewed
in a pull request and lets CI detect accidental changes to tool identifiers,
option names or output media types.

Usage:
    python scripts/export_catalog.py           # write the file
    python scripts/export_catalog.py --check   # fail if the file is stale
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "services" / "api"))

from docupro_api.engines.registry import public_catalog  # noqa: E402

TARGET = ROOT / "packages" / "shared" / "catalog.json"

#: Volatile values that depend on the host rather than on the contract.
HOST_DEPENDENT = {"available", "unavailableReason"}


def render() -> str:
    catalog = public_catalog()
    tools = []
    for tool in catalog["tools"]:
        cleaned = {key: value for key, value in tool.items() if key not in HOST_DEPENDENT}
        tools.append(cleaned)
    payload = {
        "version": 1,
        "categories": catalog["categories"],
        "tools": sorted(tools, key=lambda item: item["id"]),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the committed file is current")
    args = parser.parse_args()

    rendered = render()
    if args.check:
        if not TARGET.exists():
            print(f"missing {TARGET}", file=sys.stderr)
            return 1
        if TARGET.read_text(encoding="utf-8") != rendered:
            print(
                "packages/shared/catalog.json is out of date; run python scripts/export_catalog.py",
                file=sys.stderr,
            )
            return 1
        print("catalog contract is current")
        return 0

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(rendered, encoding="utf-8")
    tools = json.loads(rendered)["tools"]
    print(f"wrote {TARGET.relative_to(ROOT)} ({len(tools)} tools)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
