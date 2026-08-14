#!/usr/bin/env python3
"""Verify measured generated-gateway error behavior before release."""

import argparse
from pathlib import Path

import yaml


ERRORS = Path(__file__).resolve().parents[1] / "contracts/v1/http/kong-3.8-errors.yaml"
REQUIRED_DOMAIN_CASES = {"plans_validation": 400, "member_forbidden": 403, "plans_not_found": 404}
REQUIRED_DETERMINISTIC_CASES = {"deterministic_500": 500, "deterministic_503": 503}
SAFE_500_BODY = '{"code":13, "message":"Internal server error", "details":[]}'
SAFE_503_BODY = '{"code":14, "message":"Upstream service unavailable", "details":[]}'


def given_error_contract_when_checked_then_requires_measured_gateway_behavior() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", action="store_true")
    release = parser.parse_args().release
    document = yaml.safe_load(ERRORS.read_text())
    measurement = document.get("measurement", {})

    if document.get("kong", {}).get("version") != 3.8:
        raise SystemExit("Kong error evidence must target Kong 3.8")
    if measurement.get("runtime") != "generated-go-grpc-gateway":
        raise SystemExit("Kong error evidence must name generated-go-grpc-gateway")
    if measurement.get("status") != "measured-stage-3-generated-gateway":
        raise SystemExit("Kong error evidence must record measured generated-gateway behavior")

    observed = measurement.get("observed", {})
    for name, status in REQUIRED_DOMAIN_CASES.items():
        case = observed.get(name, {})
        if case.get("http_status") != status or not case.get("x_error_code") or not case.get("cors_x_error_code_browser_readable"):
            raise SystemExit(f"missing browser-visible domain error observation: {name}")

    for name, status in REQUIRED_DETERMINISTIC_CASES.items():
        case = observed.get(name, {})
        if case == "skipped-no-fixture-input":
            if release:
                raise SystemExit(f"release blocked: {name} remains unmeasured")
            continue
        if not isinstance(case, dict) or case.get("http_status") != status:
            raise SystemExit(f"invalid deterministic error observation: {name}")
        if case.get("contains_internal_exception_text") is not False:
            raise SystemExit(f"unsanitized deterministic error observation: {name}")
        if name == "deterministic_500" and (
            case.get("body") != SAFE_500_BODY
            or case.get("x_error_code") != "INTERNAL"
            or case.get("cors_x_error_code_browser_readable") is not True
        ):
            raise SystemExit("invalid browser-safe deterministic 500 observation")
        if name == "deterministic_503" and (
            case.get("body") != SAFE_503_BODY
            or case.get("x_error_code") != "absent"
            or case.get("cors_status_and_body_browser_readable") is not True
        ):
            raise SystemExit("invalid browser-safe deterministic 503 observation")

    if release and document.get("release_ready") is not True:
        raise SystemExit("release blocked: Kong error evidence is not release-ready")
    print("given measured generated-gateway errors when checked then release readiness is enforced")


if __name__ == "__main__":
    given_error_contract_when_checked_then_requires_measured_gateway_behavior()
