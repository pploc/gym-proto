#!/usr/bin/env python3
"""Verify generated service OpenAPI documents match canonical HTTP annotations."""

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
OPERATIONS = ROOT / "contracts/v1/http/active-operations.yaml"
CANONICAL_DOCUMENT = ROOT / "openapi/gym-active-api.openapi.yaml"
CANDIDATE_VERSION = "7.0.1-candidate"
METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
SERVICE_DOCUMENTS = {
    "identity": {
        "path": ROOT / "openapi/identity/v1/identity.openapi.yaml",
        "selector_prefix": "identity.v1.",
    },
    "member": {
        "path": ROOT / "openapi/member/v1/member.openapi.yaml",
        "selector_prefix": "member.v1.",
    },
    "plans": {
        "path": ROOT / "openapi/plans/v1/plans.openapi.yaml",
        "selector_prefix": "plans.v1.",
    },
    "checkin": {
        "path": ROOT / "openapi/checkin/v1/checkin.openapi.yaml",
        "selector_prefix": "checkin.v1.",
    },
}
WORKLOAD_OPERATION_IDS = {
    "MemberService_ValidateMembership",
    "MemberService_ListMembersByStatus",
    "PlansService_GetActiveGym",
    "PlansService_ResolvePurchasablePlan",
    "PlansService_ValidateCheckInGym",
}


def expected_operations() -> list[dict]:
    operations = yaml.safe_load(OPERATIONS.read_text())["operations"]
    seen = set()
    selectors = set()
    for operation in operations:
        key = (operation["method"].lower(), operation["path"])
        if operation["method"] not in METHODS:
            raise ValueError(f"unsupported HTTP method: {operation['method']}")
        if key in seen:
            raise ValueError(f"duplicate active operation: {operation['method']} {operation['path']}")
        if operation["selector"] in selectors:
            raise ValueError(f"duplicate active selector: {operation['selector']}")
        seen.add(key)
        selectors.add(operation["selector"])
    return operations


def openapi_json_path(path: str) -> str:
    return re.sub(
        r"{([^}]+)}",
        lambda match: "{" + match.group(1).split("_")[0]
        + "".join(part.title() for part in match.group(1).split("_")[1:]) + "}",
        path,
    )


def resolve_schema(schemas: dict, schema: dict) -> dict:
    reference = schema.get("$ref")
    if reference is None:
        all_of = schema.get("allOf", [])
        references = [entry.get("$ref") for entry in all_of if entry.get("$ref")]
        if not references:
            return schema
        if len(references) != 1:
            raise SystemExit(f"unsupported allOf schema references: {references}")
        reference = references[0]
    prefix = "#/components/schemas/"
    if not reference.startswith(prefix):
        raise SystemExit(f"unsupported schema reference: {reference}")
    return schemas[reference.removeprefix(prefix)]


def given_example_when_checked_then_match_schema(example: object, schema: dict, schemas: dict) -> None:
    schema = resolve_schema(schemas, schema)
    if isinstance(example, dict):
        properties = schema.get("properties", {})
        unknown = set(example) - set(properties)
        if unknown:
            raise SystemExit(f"example has unknown properties: {sorted(unknown)}")
        for name, value in example.items():
            given_example_when_checked_then_match_schema(value, properties[name], schemas)
    elif isinstance(example, list):
        item_schema = schema.get("items")
        if not item_schema:
            raise SystemExit("array example has no items schema")
        for item in example:
            given_example_when_checked_then_match_schema(item, item_schema, schemas)
    elif "enum" in schema and example not in schema["enum"]:
        raise SystemExit(f"example enum value is invalid: {example}")


def given_service_document_when_verified_then_match_partition(
    service: str, config: dict, operations: list[dict]
) -> set[str]:
    document = yaml.safe_load(config["path"].read_text())
    if not str(document.get("openapi", "")).startswith("3.0."):
        raise SystemExit(f"{service} OpenAPI version must be 3.0.x: {document.get('openapi')}")
    if document.get("info", {}).get("version") != CANDIDATE_VERSION:
        raise SystemExit(f"wrong {service} OpenAPI candidate version: {document.get('info', {}).get('version')}")

    service_operations = [
        operation
        for operation in operations
        if operation["selector"].startswith(config["selector_prefix"])
    ]
    expected = {
        (operation["method"].lower(), openapi_json_path(operation["path"])): operation
        for operation in service_operations
    }
    actual = {
        (method, path): operation
        for path, path_item in document.get("paths", {}).items()
        for method, operation in path_item.items()
        if method.upper() in METHODS
    }
    if set(actual) != set(expected):
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        raise SystemExit(
            f"{service} OpenAPI operations differ: missing={missing}, extra={extra}"
        )

    bearer = document.get("components", {}).get("securitySchemes", {}).get("BearerAuth")
    if bearer != {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}:
        raise SystemExit(f"wrong {service} BearerAuth security scheme: {bearer}")

    schemas = document.get("components", {}).get("schemas", {})
    operation_ids = set()
    for key, expected_operation in expected.items():
        operation = actual[key]
        operation_id = operation.get("operationId")
        operation_ids.add(operation_id)
        if operation_id != expected_operation["operation_id"]:
            raise SystemExit(f"wrong operationId for {service} {key}: {operation_id}")
        expected_security = [] if expected_operation["auth"] == "public" else [{"BearerAuth": []}]
        if operation.get("security", []) != expected_security:
            raise SystemExit(f"wrong security for {service} {key}: {operation.get('security')}")
        path_parameters = re.findall(r"{([^}]+)}", key[1])
        actual_parameters = [
            parameter.get("name")
            for parameter in operation.get("parameters", [])
            if parameter.get("in") == "path"
        ]
        if actual_parameters != path_parameters:
            raise SystemExit(f"wrong path parameters for {service} {key}: {actual_parameters}")
        if key[0] in {"post", "put", "patch"}:
            request_schema = (
                operation.get("requestBody", {})
                .get("content", {})
                .get("application/json", {})
                .get("schema", {})
                .get("$ref")
            )
            if not request_schema:
                raise SystemExit(f"missing JSON request body schema for {service} {key}")
            if (
                expected_operation.get("body") == "purchase"
                and request_schema != "#/components/schemas/member.v1.PurchaseMembershipBody"
            ):
                raise SystemExit(f"nested purchase body is wrong: {request_schema}")
        response_schema = (
            operation.get("responses", {})
            .get("200", {})
            .get("content", {})
            .get("application/json", {})
            .get("schema", {})
        )
        if not response_schema:
            raise SystemExit(f"missing JSON success response schema for {service} {key}")
        resolved_response_schema = resolve_schema(schemas, response_schema)
        if resolved_response_schema.get("properties"):
            example = resolved_response_schema.get("example")
            if example is None:
                raise SystemExit(f"missing native success example for {service} {key}")
            given_example_when_checked_then_match_schema(example, resolved_response_schema, schemas)

    if service == "plans":
        request = schemas["plans.v1.CreateMembershipPlanRequest"]["properties"]
        price_vnd = request["priceVnd"]
        if price_vnd.get("type") != "string":
            raise SystemExit(f"priceVnd must be string-safe Protobuf JSON int64: {price_vnd}")
        plan_type = request["planType"]
        if plan_type.get("type") != "string" or "PLAN_TYPE_MONTHLY" not in plan_type.get("enum", []):
            raise SystemExit(f"planType must use Protobuf JSON enum strings: {plan_type}")

    return operation_ids


def given_service_annotations_when_openapi_is_generated_then_documents_are_isolated() -> None:
    operations = expected_operations()
    all_operation_ids = set()
    service_counts = {}
    for service, config in SERVICE_DOCUMENTS.items():
        operation_ids = given_service_document_when_verified_then_match_partition(
            service, config, operations
        )
        overlap = all_operation_ids & operation_ids
        if overlap:
            raise SystemExit(f"operations appear in multiple OpenAPI documents: {sorted(overlap)}")
        all_operation_ids.update(operation_ids)
        service_counts[service] = len(operation_ids)

    if all_operation_ids & WORKLOAD_OPERATION_IDS:
        raise SystemExit(
            f"workload-only RPCs appear in OpenAPI: {sorted(all_operation_ids & WORKLOAD_OPERATION_IDS)}"
        )
    if len(all_operation_ids) != len(operations):
        raise SystemExit(
            f"expected {len(operations)} unique OpenAPI operations, got {len(all_operation_ids)}"
        )

    canonical = yaml.safe_load(CANONICAL_DOCUMENT.read_text())
    if canonical.get("openapi") != "3.0.3":
        raise SystemExit(f"wrong canonical OpenAPI version: {canonical.get('openapi')}")
    if canonical.get("info", {}).get("version") != CANDIDATE_VERSION:
        raise SystemExit(f"wrong canonical OpenAPI candidate version: {canonical.get('info', {}).get('version')}")
    canonical_operations = {
        operation.get("operationId")
        for path_item in canonical.get("paths", {}).values()
        for method, operation in path_item.items()
        if method.upper() in METHODS
    }
    if canonical_operations != all_operation_ids:
        raise SystemExit(
            "canonical OpenAPI operations differ: "
            f"missing={sorted(all_operation_ids - canonical_operations)}, "
            f"extra={sorted(canonical_operations - all_operation_ids)}"
        )
    if len(canonical_operations) != len(operations):
        raise SystemExit(
            f"expected {len(operations)} canonical OpenAPI operations, got {len(canonical_operations)}"
        )

    partition = ", ".join(f"{service} {count}" for service, count in service_counts.items())
    print(
        "given active annotations when service and canonical OpenAPI documents are generated "
        f"then {partition}, and canonical {len(operations)} operations match"
    )


if __name__ == "__main__":
    given_service_annotations_when_openapi_is_generated_then_documents_are_isolated()
