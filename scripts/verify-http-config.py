#!/usr/bin/env python3
"""Verify one HTTP binding source for every active RPC."""

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / "proto"
ACTIVE = ROOT / "contracts/v1/http/active-operations.yaml"
METHODS = ("get", "put", "post", "delete", "patch")
ACTIVE_PROTO_FILES = (
    PROTO / "identity/v1/identity.proto",
    PROTO / "member/v1/member.proto",
    PROTO / "plans/v1/plans.proto",
    PROTO / "checkin/v1/checkin.proto",
    PROTO / "trainer/v1/trainer.proto",
)
ACTIVE_SERVICES = {"identity", "member", "plans", "checkin", "trainer"}
WORKLOAD_ONLY = {
    "member.v1.MemberService.ValidateMembership",
    "member.v1.MemberService.ListMembersByStatus",
    "plans.v1.PlansService.GetActiveGym",
    "plans.v1.PlansService.ResolvePurchasablePlan",
    "plans.v1.PlansService.ValidateCheckInGym",
    "plans.v1.PlansService.ValidateTrainerGym",
    "identity.v1.IdentityService.ValidateTrainerAccount",
}
RETIRED = {
    "member.v1.MemberService.GetPlans",
    "member.v1.MemberService.CreateGymLocation",
    "member.v1.MemberService.UpdateGymLocation",
    "member.v1.MemberService.ListGymLocations",
    "member.v1.MemberService.GetGymLocation",
    "checkin.v1.CheckInService.GetCheckInHistory",
    "checkin.v1.CheckInService.RegisterDevice",
    "checkin.v1.CheckInService.RevokeDevice",
}


def external_rules() -> dict[str, dict]:
    rules = yaml.safe_load((PROTO / "http.yaml").read_text())["http"]["rules"]
    result = {}
    routes = {}
    for rule in rules:
        selector = rule["selector"]
        methods = [method for method in METHODS if method in rule]
        if len(methods) != 1:
            raise SystemExit(f"external rule must declare exactly one method: {rule}")
        route = (methods[0].upper(), rule[methods[0]])
        if selector in result or route in routes:
            raise SystemExit(f"duplicate external HTTP mapping: {selector} {route}")
        result[selector] = rule
        routes[route] = selector
    return result


def annotations(path: Path) -> dict[str, dict]:
    source = path.read_text()
    package = re.search(r"^package ([\w.]+);$", source, re.MULTILINE).group(1)
    service = re.search(r"service (\w+) \{", source).group(1)
    pattern = re.compile(
        r"rpc (\w+)\([^)]*\) returns \([^)]*\) \{.*?"
        r"option \(google\.api\.http\) = \{\s*"
        r"(get|put|post|delete|patch): \"([^\"]+)\"(?:\s*body: \"([^\"]+)\")?\s*\};",
        re.DOTALL,
    )
    return {
        f"{package}.{service}.{method}": {"method": http_method.upper(), "path": route, "body": body}
        for method, http_method, route, body in pattern.findall(source)
    }


def index_routes(mappings: dict[str, dict], source: str) -> None:
    routes = {}
    for selector, mapping in mappings.items():
        route = (mapping["method"], mapping["path"])
        if route in routes:
            raise SystemExit(f"duplicate HTTP route in {source}: {route} ({routes[route]}, {selector})")
        routes[route] = selector


def annotations_contain_only_allowlisted_options(path: Path, found: dict[str, dict]) -> None:
    source = path.read_text()
    options = source.count("option (google.api.http)")
    if options != len(found):
        raise SystemExit(f"unparseable google.api.http option in {path}: found={options}, parsed={len(found)}")


def given_active_annotations_when_verified_then_single_source_of_truth() -> None:
    expected = yaml.safe_load(ACTIVE.read_text())["operations"]
    expected_by_selector = {operation["selector"]: operation for operation in expected}
    if len(expected_by_selector) != len(expected):
        raise SystemExit("duplicate selector in active operations")

    inline = {}
    for path in ACTIVE_PROTO_FILES:
        parsed = annotations(path)
        annotations_contain_only_allowlisted_options(path, parsed)
        overlap = set(inline) & set(parsed)
        if overlap:
            raise SystemExit(f"duplicate inline selectors: {sorted(overlap)}")
        inline.update(parsed)
    if set(inline) != set(expected_by_selector):
        raise SystemExit(f"inline annotation selectors differ: expected={sorted(expected_by_selector)}, actual={sorted(inline)}")
    index_routes(inline, "inline annotations")
    for selector, operation in expected_by_selector.items():
        actual = inline[selector]
        if (actual["method"], actual["path"], actual["body"] or None) != (
            operation["method"], operation["path"], operation.get("body"),
        ):
            raise SystemExit(f"inline annotation differs for {selector}: {actual}")

    external = external_rules()
    dual = sorted(set(expected_by_selector) & set(external))
    if dual:
        raise SystemExit(f"active selector also exists in external YAML: {dual}")
    exposed = sorted((WORKLOAD_ONLY | RETIRED) & (set(inline) | set(external)))
    if exposed:
        raise SystemExit(f"workload or retired RPC has HTTP mapping: {exposed}")
    active_mirrors = [
        path
        for path in PROTO.glob("*/v1/*_http.yaml")
        if path.parent.parent.name in ACTIVE_SERVICES
    ]
    if active_mirrors:
        raise SystemExit(f"active service HTTP YAML mirrors must not exist: {active_mirrors}")
    print(
        "given active annotations when HTTP mappings are verified then "
        f"{len(expected)} canonical routes have no YAML duplicate"
    )


if __name__ == "__main__":
    given_active_annotations_when_verified_then_single_source_of_truth()
