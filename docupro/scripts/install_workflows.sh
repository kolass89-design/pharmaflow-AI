#!/usr/bin/env bash
# Copy the versioned workflow definitions into .github/workflows/.
# Run from the repository root. Requires a token with the `workflow` scope.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
src="$root/docupro/ci/workflows"
dst="$root/.github/workflows"

if [ ! -d "$src" ]; then
  echo "missing $src" >&2
  exit 1
fi

mkdir -p "$dst"
cp -v "$src"/*.yml "$dst/"
echo
echo "Copied $(ls -1 "$src" | wc -l) workflows to .github/workflows"
echo "Next: git add .github/workflows && git commit -m 'ci: activate pipelines' && git push"
