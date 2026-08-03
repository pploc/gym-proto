#!/usr/bin/env bash
set -euo pipefail

readonly IDENTITY_GATEWAY="gen/go/identity/v1/identity.pb.gw.go"
readonly MEMBER_GATEWAY="gen/go/member/v1/member.pb.gw.go"

for file in "$IDENTITY_GATEWAY" "$MEMBER_GATEWAY"; do
  if [[ ! -f "$file" ]]; then
    printf 'missing generated gateway file: %s\n' "$file" >&2
    exit 1
  fi
done

require_route() {
  local file=$1
  local method=$2
  local path=$3
  grep -Fq "\"/$method\"" "$file" || {
    printf 'missing generated RPC route: %s\n' "$method" >&2
    exit 1
  }
  grep -Fq "WithHTTPPathPattern(\"$path\")" "$file" || {
    printf 'missing generated HTTP path: %s\n' "$path" >&2
    exit 1
  }
}

reject_method() {
  local file=$1
  local method=$2
  if grep -Fq "$method" "$file"; then
    printf 'internal RPC unexpectedly exposed by grpc-gateway: %s\n' "$method" >&2
    exit 1
  fi
}

require_route "$IDENTITY_GATEWAY" "identity.v1.IdentityService/Register" "/api/v1/auth/register"
require_route "$IDENTITY_GATEWAY" "identity.v1.IdentityService/RefreshToken" "/api/v1/auth/refresh"
require_route "$MEMBER_GATEWAY" "member.v1.MemberService/GetMember" "/api/v1/members/{member_id}"
require_route "$MEMBER_GATEWAY" "member.v1.MemberService/GetMembershipStatus" "/api/v1/memberships/status/{member_id}"

reject_method "$MEMBER_GATEWAY" "GetMembershipStatusByUserId"
reject_method "$MEMBER_GATEWAY" "ValidateMembership"
reject_method "$MEMBER_GATEWAY" "ListMembersByStatus"

printf 'generated Identifier and Member routes match the frozen external surface\n'
