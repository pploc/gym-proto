#!/usr/bin/env bash
set -euo pipefail

readonly root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly export_dir="$root/dist/kong-proto"
readonly archive="$root/dist/kong-proto-6.0.0.tar.gz"

rm -rf "$export_dir" "$archive"
mkdir -p "$export_dir"
(
  cd "$root"
  buf export . --output "$export_dir"
)
(
  cd "$export_dir"
  find . -type f -print | LC_ALL=C sort | tar \
    --create --gzip --file "$archive" \
    --files-from=- \
    --owner=0 --group=0 --numeric-owner \
    --mode='u=rw,go=r' --mtime='UTC 1970-01-01'
)
sha256sum "$archive" > "$archive.sha256"
