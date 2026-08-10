#!/usr/bin/env python3
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
retired = {
    root / "proto/identity/v1/identity.proto": (
        r"\brpc\s+SelectGym\b",
        r"\bmessage\s+SelectGymRequest\b",
        r"\bmessage\s+SelectGymResponse\b",
    ),
    root / "proto/member/v1/member.proto": (
        r"\brpc\s+GetMembershipStatusByUserId\b",
        r"\bmessage\s+GetMembershipStatusByUserIdRequest\b",
        r"\bmessage\s+GetMembershipStatusByUserIdResponse\b",
    ),
}

for path, patterns in retired.items():
    source = path.read_text()
    for pattern in patterns:
        if re.search(pattern, source):
            raise SystemExit(f"retired Protobuf symbol reused in {path.relative_to(root)}: {pattern}")

for generated_root in (root / "gen/go", root / "gen/java"):
    if not generated_root.exists():
        continue
    for path in generated_root.rglob("*"):
        if not path.is_file():
            continue
        source = path.read_text(errors="ignore")
        for name in ("SelectGym", "GetMembershipStatusByUserId"):
            if name in source:
                raise SystemExit(f"retired symbol remains in generated output: {path.relative_to(root)}: {name}")

print("retired Protobuf RPC and message names are absent")
