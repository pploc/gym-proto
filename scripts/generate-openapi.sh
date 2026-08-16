#!/usr/bin/env bash
set -euo pipefail

readonly root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly output_dir="$root/openapi"
readonly plugin_dir="${TMPDIR:-/tmp}/gym-proto-gnostic-v0.7.1"

rm -rf "$output_dir" "$plugin_dir"
mkdir -p "$output_dir" "$plugin_dir"
GOBIN="$plugin_dir" go install github.com/google/gnostic/cmd/protoc-gen-openapi@v0.7.1
(
  cd "$root"
  PATH="$plugin_dir:$PATH" buf generate \
    --path proto/identity/v1/identity.proto \
    --path proto/member/v1/member.proto \
    --path proto/plans/v1/plans.proto \
    --path proto/checkin/v1/checkin.proto \
    --template "$root/buf.openapi.gen.yaml"
)
python3 "$root/scripts/merge-openapi.py"
rm -rf "$plugin_dir"
