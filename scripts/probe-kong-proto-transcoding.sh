#!/usr/bin/env bash
set -euo pipefail

readonly root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly bundle="$root/dist/kong-proto"
readonly temp_dir="$(mktemp -d)"
readonly container="gym-kong-proto-transcoding-$$"
trap 'docker rm -f "$container" >/dev/null 2>&1 || true; rm -rf "$temp_dir"' EXIT

cat > "$temp_dir/kong.yml" <<'EOF'
_format_version: "3.0"
services:
  - name: member-source-proto
    protocol: grpc
    host: 127.0.0.1
    port: 50051
    routes:
      - name: member-source-proto
        protocols: [http]
        methods: [GET]
        paths: ["/api/v1/members/proto-smoke"]
        plugins:
          - name: grpc-gateway
            config:
              proto: /proto/member/v1/member.proto
  - name: plans-source-proto
    protocol: grpc
    host: 127.0.0.1
    port: 50051
    routes:
      - name: plans-source-proto
        protocols: [http]
        methods: [POST]
        paths: ["/api/v1/gyms"]
        plugins:
          - name: grpc-gateway
            config:
              proto: /proto/plans/v1/plans.proto
EOF

docker run --detach --rm --name "$container" \
  -p 127.0.0.1::8000 \
  -e KONG_DATABASE=off \
  -e KONG_DECLARATIVE_CONFIG=/work/kong.yml \
  -e KONG_PLUGINS=bundled,grpc-gateway \
  -v "$temp_dir/kong.yml:/work/kong.yml:ro" \
  -v "$bundle:/proto:ro" \
  -v "$bundle/buf:/usr/local/kong/include/buf:ro" \
  -v "$bundle/google/api:/usr/local/kong/include/google/api:ro" \
  kong:3.8-ubuntu >/dev/null

port="$(docker port "$container" 8000/tcp)"
port="${port##*:}"
base="http://127.0.0.1:$port"

request_until_ready() {
  local method="$1"
  local path="$2"
  local body="${3:-}"
  local status

  for _ in {1..30}; do
    if [ -n "$body" ]; then
      status="$(curl --silent --output /dev/null --write-out '%{http_code}' \
        --header 'Content-Type: application/json' --request "$method" --data "$body" "$base$path" || true)"
    else
      status="$(curl --silent --output /dev/null --write-out '%{http_code}' \
        --request "$method" "$base$path" || true)"
    fi
    [ "$status" = "500" ] && return 0
    sleep 1
  done

  printf 'expected Kong grpc-gateway parser rejection for %s %s; got HTTP %s\n' "$method" "$path" "$status" >&2
  docker logs "$container" >&2
  return 1
}

request_until_ready GET /api/v1/members/proto-smoke
request_until_ready POST /api/v1/gyms '{"chainId":"chain-smoke","name":"Smoke","address":"1 Test Way","city":"Test"}'

logs="$temp_dir/kong.log"
docker logs "$container" >"$logs" 2>&1
matches="$(grep -c 'buf/validate/validate.proto:535:9: field name expected' "$logs" || true)"
if [ "$matches" -lt 2 ]; then
  printf 'expected Member and Plans parser failures; observed %s\n' "$matches" >&2
  docker logs "$container" >&2
  exit 1
fi

printf '%s\n' 'given current source protobufs when Kong 3.8 grpc-gateway parses Member and Plans routes then both reject buf/validate/validate.proto at line 535'
