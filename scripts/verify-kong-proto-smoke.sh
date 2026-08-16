#!/usr/bin/env bash
set -euo pipefail

readonly root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly bundle="$root/dist/kong-proto"
readonly temp_dir="$(mktemp -d)"
readonly container="gym-kong-proto-smoke-$$"
trap 'docker rm -f "$container" >/dev/null 2>&1 || true; rm -rf "$temp_dir"' EXIT

cat > "$temp_dir/kong.yml" <<'EOF'
_format_version: "3.0"
services:
  - name: absent-grpc-upstream
    protocol: grpc
    host: 127.0.0.1
    port: 50051
    routes:
      - name: member-source-proto
        protocols: [http]
        paths: ["/member"]
        plugins:
          - name: grpc-gateway
            config:
              proto: /proto/member/v1/member.proto
      - name: plans-source-proto
        protocols: [http]
        paths: ["/plans"]
        plugins:
          - name: grpc-gateway
            config:
              proto: /proto/plans/v1/plans.proto
      - name: checkin-source-proto
        protocols: [http]
        paths: ["/checkin"]
        plugins:
          - name: grpc-gateway
            config:
              proto: /proto/checkin/v1/checkin.proto
EOF

docker run --detach --rm --name "$container" \
  --network none \
  -e KONG_DATABASE=off \
  -e KONG_DECLARATIVE_CONFIG=/work/kong.yml \
  -e KONG_PLUGINS=bundled,grpc-gateway \
  -v "$temp_dir/kong.yml:/work/kong.yml:ro" \
  -v "$bundle:/proto:ro" \
  -v "$bundle/buf:/usr/local/kong/include/buf:ro" \
  -v "$bundle/google/api:/usr/local/kong/include/google/api:ro" \
  kong:3.8-ubuntu >/dev/null

for _ in {1..30}; do
  if docker exec "$container" kong health >/dev/null 2>&1; then
    printf 'given source protobuf bundle when Kong 3.8 starts then Member, Plans, and Check-in roots parse\n'
    exit 0
  fi
  sleep 1
done

docker logs "$container" >&2
exit 1
