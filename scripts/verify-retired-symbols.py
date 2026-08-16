#!/usr/bin/env python3
import re
from pathlib import Path

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
    root / "proto/checkin/v1/checkin.proto": (
        r"\brpc\s+GetCheckInHistory\b",
        r"\bmessage\s+GetCheckInHistoryRequest\b",
        r"\bmessage\s+GetCheckInHistoryResponse\b",
        r"\brpc\s+RegisterDevice\b",
        r"\bmessage\s+RegisterDeviceRequest\b",
        r"\bmessage\s+RegisterDeviceResponse\b",
        r"\brpc\s+RevokeDevice\b",
        r"\bmessage\s+RevokeDeviceRequest\b",
        r"\bmessage\s+RevokeDeviceResponse\b",
        r"\b(?:string|bytes|int32|int64|uint32|uint64)\s+device_id\s*=",
    ),
}
generated_retired = {
    "identity/v1": ("SelectGym",),
    "member/v1": ("GetMembershipStatusByUserId",),
    "checkin/v1": ("GetCheckInHistory", "RegisterDevice", "RevokeDevice"),
}

for path, patterns in retired.items():
    source = path.read_text()
    for pattern in patterns:
        if re.search(pattern, source):
            raise SystemExit(f"retired Protobuf symbol reused in {path.relative_to(root)}: {pattern}")

checkin = (root / "proto/checkin/v1/checkin.proto").read_text()
if not re.search(r"message\s+ProcessScanRequest\s*\{\s*reserved\s+1;\s*reserved\s+\"member_id\";", checkin):
    raise SystemExit("ProcessScanRequest must reserve removed member_id field 1 and name")
if not re.search(r"message\s+GetDisplayQrPayloadRequest\s*\{\s*reserved\s+1;\s*reserved\s+\"device_id\";", checkin):
    raise SystemExit("GetDisplayQrPayloadRequest must reserve removed device_id field 1 and name")
if not re.search(r"message\s+GetDisplayQrPayloadResponse\s*\{.*?reserved\s+2;\s*reserved\s+\"device_id\";", checkin, re.DOTALL):
    raise SystemExit("GetDisplayQrPayloadResponse must reserve removed device_id field 2 and name")

event = (root / "proto/events/v1/checkin_events.proto").read_text()
if not re.search(r"message\s+CheckInRecordedEvent\s*\{\s*reserved\s+3;\s*reserved\s+\"device_id\";", event):
    raise SystemExit("CheckInRecordedEvent must reserve removed device_id field 3 and name")

for generated_root in (root / "gen/go", root / "gen/java"):
    if not generated_root.exists():
        continue
    for package, names in generated_retired.items():
        package_root = generated_root / package
        if generated_root.name == "java":
            package_root = generated_root / "com/gym/proto" / package
        if not package_root.exists():
            continue
        for path in package_root.rglob("*"):
            if not path.is_file():
                continue
            source = path.read_text(errors="ignore")
            for name in names:
                if name in source:
                    raise SystemExit(f"retired symbol remains in generated output: {path.relative_to(root)}: {name}")

print("retired Protobuf RPC, message, and device-field names are absent; removed fields remain reserved")
