#!/usr/bin/env bash
set -euo pipefail

bad=$(grep -rIniE 'edusync|edu-sync|edu_sync|acadentrix|\bteams?\b' \
  --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=dist --exclude-dir=.venv \
  --exclude=package-lock.json --exclude=check-legacy-names.sh . || true)

if [ -n "$bad" ]; then
  echo "Legacy names or banned words found:"
  echo "$bad"
  exit 1
fi

echo "Legacy-name check passed: 0 matches found."
