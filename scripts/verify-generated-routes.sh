#!/usr/bin/env bash
set -euo pipefail

readonly IDENTITY_GATEWAY="gen/go/identity/v1/identity.pb.gw.go"
readonly MEMBER_GATEWAY="gen/go/member/v1/member.pb.gw.go"
readonly PLANS_GATEWAY="gen/go/plans/v1/plans.pb.gw.go"

for file in "$IDENTITY_GATEWAY" "$MEMBER_GATEWAY" "$PLANS_GATEWAY"; do
  if [[ ! -f "$file" ]]; then
    printf 'missing generated gateway file: %s\n' "$file" >&2
    exit 1
  fi
done

require_route() {
  local file=$1
  local method=$2
  local path=$3
  local expected="\"/$method\", runtime.WithHTTPPathPattern(\"$path\")"
  local count
  count=$(grep -Fc "$expected" "$file" || true)
  if [[ "$count" -ne 2 ]]; then
    printf 'generated route must occur exactly twice: %s %s (got %s)\n' \
      "$method" "$path" "$count" >&2
    exit 1
  fi
}

reject_method() {
  local file=$1
  local method=$2
  if grep -Fq "$method" "$file"; then
    printf 'RPC unexpectedly exposed by grpc-gateway: %s\n' "$method" >&2
    exit 1
  fi
}

assert_route_count() {
  local file=$1
  local expected=$2
  local actual
  actual=$(grep -c 'WithHTTPPathPattern' "$file" || true)
  if [[ "$actual" -ne "$expected" ]]; then
    printf 'unexpected generated route count in %s: expected %s, got %s\n' \
      "$file" "$expected" "$actual" >&2
    exit 1
  fi
}

assert_unique_routes() {
  local file=$1
  local dups
  # grpc-gateway emits each method+path pair twice (unary + stream helpers).
  dups=$(grep -oE '"/[^"]+", runtime.WithHTTPPathPattern\("[^"]*"\)' "$file" \
    | sort | uniq -c | awk '$1 != 2 {print}')
  if [[ -n "$dups" ]]; then
    printf 'unexpected generated route multiplicity in %s:\n%s\n' "$file" "$dups" >&2
    exit 1
  fi
}

require_route "$IDENTITY_GATEWAY" "identity.v1.IdentityService/Register" "/api/v1/auth/register"
require_route "$IDENTITY_GATEWAY" "identity.v1.IdentityService/RefreshToken" "/api/v1/auth/refresh"
require_route "$IDENTITY_GATEWAY" "identity.v1.IdentityService/VerifyEmail" "/api/v1/auth/email/verify"
require_route "$IDENTITY_GATEWAY" "identity.v1.IdentityService/SelectGym" "/api/v1/auth/gym"
require_route "$IDENTITY_GATEWAY" "identity.v1.IdentityService/CreateTrainerAccount" "/api/v1/admin/trainers"
require_route "$IDENTITY_GATEWAY" "identity.v1.IdentityService/SuspendUser" "/api/v1/admin/users/{user_id}/suspend"
require_route "$IDENTITY_GATEWAY" "identity.v1.IdentityService/ListUsers" "/api/v1/admin/users"
require_route "$MEMBER_GATEWAY" "member.v1.MemberService/GetMember" "/api/v1/members/{member_id}"
require_route "$MEMBER_GATEWAY" "member.v1.MemberService/GetMembershipStatus" "/api/v1/memberships/status/{member_id}"
require_route "$PLANS_GATEWAY" "plans.v1.PlansService/CreateGymLocation" "/api/v1/gyms"
require_route "$PLANS_GATEWAY" "plans.v1.PlansService/UpdateGymLocation" "/api/v1/gyms/{id}"
require_route "$PLANS_GATEWAY" "plans.v1.PlansService/GetGymLocation" "/api/v1/gyms/{id}"
require_route "$PLANS_GATEWAY" "plans.v1.PlansService/ListGymLocations" "/api/v1/gyms"
require_route "$PLANS_GATEWAY" "plans.v1.PlansService/CreateMembershipPlan" "/api/v1/gyms/{gym_id}/plans"
require_route "$PLANS_GATEWAY" "plans.v1.PlansService/UpdateMembershipPlan" "/api/v1/plans/{id}"
require_route "$PLANS_GATEWAY" "plans.v1.PlansService/GetMembershipPlan" "/api/v1/plans/{id}"
require_route "$PLANS_GATEWAY" "plans.v1.PlansService/ListMembershipPlans" "/api/v1/gyms/{gym_id}/plans"

reject_method "$MEMBER_GATEWAY" "GetMembershipStatusByUserId"
reject_method "$MEMBER_GATEWAY" "ValidateMembership"
reject_method "$MEMBER_GATEWAY" "ListMembersByStatus"
reject_method "$MEMBER_GATEWAY" "GetPlans"
reject_method "$MEMBER_GATEWAY" "CreateGymLocation"
reject_method "$MEMBER_GATEWAY" "UpdateGymLocation"
reject_method "$MEMBER_GATEWAY" "ListGymLocations"
reject_method "$MEMBER_GATEWAY" "GetGymLocation"
reject_method "$PLANS_GATEWAY" "GetActiveGym"
reject_method "$PLANS_GATEWAY" "ResolvePurchasablePlan"

assert_route_count "$PLANS_GATEWAY" 16
for file in "$IDENTITY_GATEWAY" "$MEMBER_GATEWAY" "$PLANS_GATEWAY"; do
  assert_unique_routes "$file"
done

printf 'generated Identifier, Member, and exact eight Plans routes match the frozen external surface\n'
