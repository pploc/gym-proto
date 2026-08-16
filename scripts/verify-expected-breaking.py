#!/usr/bin/env python3
"""Require exactly the approved v7 break against immutable v6.0.1."""

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = Counter(
    {
        ("MESSAGE_NO_DELETE", 'Previously present message "GetCheckInHistoryRequest" was deleted from file.'): 1,
        ("MESSAGE_NO_DELETE", 'Previously present message "GetCheckInHistoryResponse" was deleted from file.'): 1,
        ("MESSAGE_NO_DELETE", 'Previously present message "RegisterDeviceRequest" was deleted from file.'): 1,
        ("MESSAGE_NO_DELETE", 'Previously present message "RegisterDeviceResponse" was deleted from file.'): 1,
        ("MESSAGE_NO_DELETE", 'Previously present message "RevokeDeviceRequest" was deleted from file.'): 1,
        ("MESSAGE_NO_DELETE", 'Previously present message "RevokeDeviceResponse" was deleted from file.'): 1,
        ("RPC_NO_DELETE", 'Previously present RPC "GetCheckInHistory" on service "CheckInService" was deleted.'): 1,
        ("RPC_NO_DELETE", 'Previously present RPC "RegisterDevice" on service "CheckInService" was deleted.'): 1,
        ("RPC_NO_DELETE", 'Previously present RPC "RevokeDevice" on service "CheckInService" was deleted.'): 1,
        ("FIELD_NO_DELETE", 'Previously present field "1" with name "member_id" on message "ProcessScanRequest" was deleted.'): 1,
        ("FIELD_SAME_CARDINALITY", 'Field "4" with name "checked_in_at" on message "CheckInRecord" changed cardinality from "optional with implicit presence" to "optional with explicit presence".'): 1,
        ("FIELD_SAME_TYPE", 'Field "4" with name "checked_in_at" on message "CheckInRecord" changed type from "string" to "message".'): 1,
        ("FIELD_NO_DELETE", 'Previously present field "1" with name "device_id" on message "GetDisplayQrPayloadRequest" was deleted.'): 1,
        ("FIELD_SAME_CARDINALITY", 'Field "2" with name "active_at" on message "SignedQrPayload" changed cardinality from "optional with implicit presence" to "optional with explicit presence".'): 1,
        ("FIELD_SAME_TYPE", 'Field "2" with name "active_at" on message "SignedQrPayload" changed type from "int64" to "message".'): 1,
        ("FIELD_SAME_CARDINALITY", 'Field "3" with name "expires_at" on message "SignedQrPayload" changed cardinality from "optional with implicit presence" to "optional with explicit presence".'): 1,
        ("FIELD_SAME_TYPE", 'Field "3" with name "expires_at" on message "SignedQrPayload" changed type from "int64" to "message".'): 1,
        ("FIELD_NO_DELETE", 'Previously present field "2" with name "device_id" on message "GetDisplayQrPayloadResponse" was deleted.'): 1,
        ("FIELD_SAME_CARDINALITY", 'Field "3" with name "activated_at" on message "RotateGymQrRootKeyResponse" changed cardinality from "optional with implicit presence" to "optional with explicit presence".'): 1,
        ("FIELD_SAME_TYPE", 'Field "3" with name "activated_at" on message "RotateGymQrRootKeyResponse" changed type from "int64" to "message".'): 1,
        ("FIELD_NO_DELETE", 'Previously present field "3" with name "device_id" on message "CheckInRecordedEvent" was deleted.'): 1,
        ("FIELD_SAME_CARDINALITY", 'Field "4" with name "checked_in_at" on message "CheckInRecordedEvent" changed cardinality from "optional with implicit presence" to "optional with explicit presence".'): 1,
        ("FIELD_SAME_TYPE", 'Field "4" with name "checked_in_at" on message "CheckInRecordedEvent" changed type from "int64" to "message".'): 1,
        ("FIELD_NO_DELETE", 'Previously present field "1" with name "member_id" on message "ValidateMembershipRequest" was deleted.'): 1,
    }
)


def given_v7_candidate_when_compared_then_only_approved_breaks_exist(stable_tag: str) -> None:
    command = [
        "buf",
        "breaking",
        str(ROOT / "proto"),
        "--against",
        f"{ROOT / '.git'}#tag={stable_tag},subdir=proto",
        "--error-format=json",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode not in {0, 100}:
        raise SystemExit(result.stderr or result.stdout or f"buf breaking exited {result.returncode}")

    diagnostics = Counter()
    for line in result.stdout.splitlines():
        if line.strip():
            diagnostic = json.loads(line)
            diagnostics[(diagnostic["type"], diagnostic["message"])] += 1

    if diagnostics != EXPECTED:
        missing = list((EXPECTED - diagnostics).elements())
        extra = list((diagnostics - EXPECTED).elements())
        raise SystemExit(f"v7 breaking diagnostics differ: missing={missing}, extra={extra}")
    print(f"given v7 candidate when compared with {stable_tag} then exactly {sum(EXPECTED.values())} approved breaks remain")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--against-tag", default="v6.0.1")
    arguments = parser.parse_args()
    given_v7_candidate_when_compared_then_only_approved_breaks_exist(arguments.against_tag)
