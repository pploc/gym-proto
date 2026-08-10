#!/usr/bin/env python3
from pathlib import Path

import yaml

root = Path(__file__).resolve().parents[1] / "proto"
combined = yaml.safe_load((root / "http.yaml").read_text())["http"]["rules"]
legacy = []
for path in sorted(root.glob("*/v1/*_http.yaml")):
    legacy.extend(yaml.safe_load(path.read_text())["http"]["rules"])


def index_unique(rules, source):
    by_selector = {}
    by_route = {}
    for rule in rules:
        selector = rule["selector"]
        if selector in by_selector:
            raise SystemExit(f"duplicate selector in {source}: {selector}")
        by_selector[selector] = rule

        methods = [method for method in ("get", "put", "post", "delete", "patch") if method in rule]
        if len(methods) != 1:
            raise SystemExit(f"HTTP rule must declare exactly one method in {source}: {rule}")
        route = (methods[0].upper(), rule[methods[0]])
        if route in by_route:
            raise SystemExit(
                f"duplicate HTTP route in {source}: {route[0]} {route[1]} "
                f"({by_route[route]}, {selector})"
            )
        by_route[route] = selector
    return by_selector


combined_by_selector = index_unique(combined, "proto/http.yaml")
legacy_by_selector = index_unique(legacy, "service HTTP configs")
if combined_by_selector != legacy_by_selector:
    missing = sorted(legacy_by_selector.keys() - combined_by_selector.keys())
    extra = sorted(combined_by_selector.keys() - legacy_by_selector.keys())
    changed = sorted(
        selector
        for selector in combined_by_selector.keys() & legacy_by_selector.keys()
        if combined_by_selector[selector] != legacy_by_selector[selector]
    )
    raise SystemExit(
        f"consolidated mappings differ: missing={missing}, extra={extra}, changed={changed}"
    )

member_public = {
    "member.v1.MemberService.GetMember": {"get": "/api/v1/members/{member_id}"},
    "member.v1.MemberService.UpdateProfile": {"put": "/api/v1/members/{member_id}", "body": "*"},
    "member.v1.MemberService.ListMembers": {"get": "/api/v1/gyms/{gym_id}/members"},
    "member.v1.MemberService.PurchaseMembership": {
        "post": "/api/v1/gyms/{gym_id}/memberships/purchase",
        "body": "purchase",
    },
    "member.v1.MemberService.PauseMembership": {
        "post": "/api/v1/gyms/{gym_id}/members/{member_id}/membership:pause",
        "body": "*",
    },
    "member.v1.MemberService.ResumeMembership": {
        "post": "/api/v1/gyms/{gym_id}/members/{member_id}/membership:resume",
        "body": "*",
    },
    "member.v1.MemberService.GetMembershipStatus": {
        "get": "/api/v1/gyms/{gym_id}/members/{member_id}/membership"
    },
}
actual_member = {
    selector: {key: value for key, value in rule.items() if key != "selector"}
    for selector, rule in combined_by_selector.items()
    if selector.startswith("member.v1.MemberService.")
}
if actual_member != member_public:
    raise SystemExit(f"Member HTTP surface differs: expected={member_public}, actual={actual_member}")

plans_public = {
    "plans.v1.PlansService.CreateGymLocation": {"post": "/api/v1/gyms", "body": "*"},
    "plans.v1.PlansService.UpdateGymLocation": {"put": "/api/v1/gyms/{id}", "body": "*"},
    "plans.v1.PlansService.GetGymLocation": {"get": "/api/v1/gyms/{id}"},
    "plans.v1.PlansService.ListGymLocations": {"get": "/api/v1/gyms"},
    "plans.v1.PlansService.CreateMembershipPlan": {
        "post": "/api/v1/gyms/{gym_id}/plans",
        "body": "*",
    },
    "plans.v1.PlansService.UpdateMembershipPlan": {"put": "/api/v1/plans/{id}", "body": "*"},
    "plans.v1.PlansService.GetMembershipPlan": {"get": "/api/v1/plans/{id}"},
    "plans.v1.PlansService.ListMembershipPlans": {"get": "/api/v1/gyms/{gym_id}/plans"},
}
actual_plans = {
    selector: {key: value for key, value in rule.items() if key != "selector"}
    for selector, rule in combined_by_selector.items()
    if selector.startswith("plans.v1.PlansService.")
}
if actual_plans != plans_public:
    raise SystemExit(f"Plans HTTP surface differs: expected={plans_public}, actual={actual_plans}")

internal = {
    "member.v1.MemberService.ValidateMembership",
    "member.v1.MemberService.ListMembersByStatus",
    "plans.v1.PlansService.GetActiveGym",
    "plans.v1.PlansService.ResolvePurchasablePlan",
}
moved_member = {
    "member.v1.MemberService.GetPlans",
    "member.v1.MemberService.CreateGymLocation",
    "member.v1.MemberService.UpdateGymLocation",
    "member.v1.MemberService.ListGymLocations",
    "member.v1.MemberService.GetGymLocation",
}
for label, selectors in (("internal", internal), ("moved Member", moved_member)):
    exposed = sorted(selectors & combined_by_selector.keys())
    if exposed:
        raise SystemExit(f"{label} RPCs have HTTP mappings: {exposed}")

print(
    f"consolidated mapping preserves all {len(legacy)} intentional HTTP rules, "
    "including the exact eight-route Plans surface"
)
