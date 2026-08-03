#!/usr/bin/env python3
from pathlib import Path

import yaml

root = Path(__file__).resolve().parents[1] / "proto"
combined = yaml.safe_load((root / "http.yaml").read_text())["http"]["rules"]
legacy = []
for path in sorted(root.glob("*/v1/*_http.yaml")):
    legacy.extend(yaml.safe_load(path.read_text())["http"]["rules"])

combined_by_selector = {rule["selector"]: rule for rule in combined}
legacy_by_selector = {rule["selector"]: rule for rule in legacy}
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

internal = {
    "member.v1.MemberService.GetMembershipStatusByUserId",
    "member.v1.MemberService.ValidateMembership",
    "member.v1.MemberService.ListMembersByStatus",
}
exposed = sorted(internal & combined_by_selector.keys())
if exposed:
    raise SystemExit(f"internal RPCs have HTTP mappings: {exposed}")

print(f"consolidated mapping preserves all {len(legacy)} intentional HTTP rules")
