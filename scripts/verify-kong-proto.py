#!/usr/bin/env python3
"""Verify Kong source protobuf bundle contains active roots and imports."""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "dist/kong-proto"
ACTIVE_ROOTS = (
    "identity/v1/identity.proto",
    "member/v1/member.proto",
    "plans/v1/plans.proto",
    "checkin/v1/checkin.proto",
    "trainer/v1/trainer.proto",
)
REQUIRED = ACTIVE_ROOTS + (
    "common/v1/common.proto",
    "google/api/annotations.proto",
    "google/api/http.proto",
    "buf/validate/validate.proto",
)


def given_exported_bundle_when_verified_then_keep_kong_roots_and_imports() -> None:
    missing = [relative_path for relative_path in REQUIRED if not (BUNDLE / relative_path).is_file()]
    if missing:
        raise SystemExit(f"Kong protobuf bundle missing files: {missing}")
    for relative_path in ACTIVE_ROOTS:
        source = (BUNDLE / relative_path).read_text()
        if relative_path != "common/v1/common.proto" and 'import "google/api/annotations.proto";' not in source:
            raise SystemExit(f"Kong active root lacks HTTP annotations import: {relative_path}")
    print("given exported protobuf sources when Kong bundle is verified then active roots and imports remain mountable")


if __name__ == "__main__":
    given_exported_bundle_when_verified_then_keep_kong_roots_and_imports()
