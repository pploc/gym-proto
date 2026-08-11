#!/usr/bin/env python3
"""Verify generated service OpenAPI documents match canonical HTTP annotations."""

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
OPERATIONS = ROOT / "contracts/v1/http/active-operations.yaml"
METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
SERVICE_DOCUMENTS = {
    "identity": {
        "path": ROOT / "openapi/identity/v1/identity.openapi.yaml",
        "selector_prefix": "identity.v1.",
        "operation_count": 12,
    },
    "member": {
        "path": ROOT / "openapi/member/v1/member.openapi.yaml",
        "selector_prefix": "member.v1.",
        "operation_count": 7,
    },
    "plans": {
        "path": ROOT / "openapi/plans/v1/plans.openapi.yaml",
        "selector_prefix": "plans.v1.",
        "operation_count": 8,
    },
}
WORKLOAD_OPERATION_IDS = {
    "MemberService_ValidateMembership",
    "MemberService_ListMembersByStatus",
    "PlansService_GetActiveGym",
    "PlansService_ResolvePurchasablePlan",
}


def expected_operations() -> list[dict]:
    operations = yaml.safe_load(OPERATIONS.read_text())["operations"]
    if len(operations) != 27:
        raise ValueError(f"expected 27 active operations, got {len(operations)}")
    seen = set()
    for operation in operations:
        key = (operation["method"].lower(), operation["path"])
        if operation["method"] not in METHODS:
            raise ValueError(f"unsupported HTTP method: {operation['method']}")
        if key in seen:
            raise ValueError(f"duplicate active operation: {operation['method']} {operation['path']}")
        seen.add(key)
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
    if not reference:
        return schema
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
    if document.get("info", {}).get("version") != "6.0.0-candidate":
        raise SystemExit(f"wrong {service} OpenAPI candidate version: {document.get('info', {}).get('version')}")

    service_operations = [
        operation
        for operation in operations
        if operation["selector"].startswith(config["selector_prefix"])
    ]
    if len(service_operations) != config["operation_count"]:
        raise SystemExit(
            f"wrong expected {service} operation count: {len(service_operations)}"
        )
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
    for service, config in SERVICE_DOCUMENTS.items():
        operation_ids = given_service_document_when_verified_then_match_partition(
            service, config, operations
        )
        overlap = all_operation_ids & operation_ids
        if overlap:
            raise SystemExit(f"operations appear in multiple OpenAPI documents: {sorted(overlap)}")
        all_operation_ids.update(operation_ids)

    if all_operation_ids & WORKLOAD_OPERATION_IDS:
        raise SystemExit(
            f"workload-only RPCs appear in OpenAPI: {sorted(all_operation_ids & WORKLOAD_OPERATION_IDS)}"
        )
    if len(all_operation_ids) != 27:
        raise SystemExit(f"expected 27 unique OpenAPI operations, got {len(all_operation_ids)}")

    print(
        "given active annotations when service OpenAPI documents are generated "
        "then Identity 12, Member 7, and Plans 8 operations match"
    )


if __name__ == "__main__":
    given_service_annotations_when_openapi_is_generated_then_documents_are_isolated()
