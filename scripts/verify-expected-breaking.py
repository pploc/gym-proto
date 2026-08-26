#!/usr/bin/env python3
"""Require exactly the approved G12 break against immutable v7.0.2."""

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = Counter([
    ("ENUM_NO_DELETE", 'Previously present enum "BookingStatus" was deleted from file.'),
    ("ENUM_VALUE_NO_DELETE", 'Previously present enum value "2" on enum "TrainerStatus" was deleted.'),
    ("FIELD_NO_DELETE", 'Previously present field "2" with name "affected_booking_count" on message "SuspendTrainerResponse" was deleted.'),
    ("FIELD_NO_DELETE", 'Previously present field "4" with name "hourly_rate" on message "CreateTrainerRequest" was deleted.'),
    ("FIELD_NO_DELETE", 'Previously present field "4" with name "is_recurring" on message "AvailabilitySlot" was deleted.'),
    ("FIELD_NO_DELETE", 'Previously present field "9" with name "hourly_rate_vnd" on message "CreateTrainerResponse" was deleted.'),
    ("FIELD_NO_DELETE", 'Previously present field "9" with name "hourly_rate_vnd" on message "GetTrainerProfileResponse" was deleted.'),
    ("FIELD_NO_DELETE", 'Previously present field "9" with name "hourly_rate_vnd" on message "UpdateMyProfileResponse" was deleted.'),
    *[("MESSAGE_NO_DELETE", f'Previously present message "{name}" was deleted from file.') for name in (
        "AcceptBookingRequest", "AcceptBookingResponse", "CancelBookingRequest", "CancelBookingResponse",
        "CompleteBookingRequest", "CompleteBookingResponse", "CreateBookingRequest", "CreateBookingResponse",
        "GetCoachingHistoryRequest", "GetCoachingHistoryResponse", "GetMyBookingsRequest", "GetMyBookingsResponse",
        "RejectBookingRequest", "RejectBookingResponse",
    )],
    *[("RPC_NO_DELETE", f'Previously present RPC "{name}" on service "TrainerService" was deleted.') for name in (
        "AcceptBooking", "CancelBooking", "CompleteBooking", "CreateBooking", "GetCoachingHistory",
        "GetMyBookings", "RejectBooking",
    )],
])


def given_v8_candidate_when_compared_then_only_approved_breaks_exist(stable_tag: str) -> None:
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
        raise SystemExit(f"v8 breaking diagnostics differ: missing={missing}, extra={extra}")
    print(f"given v8 candidate when compared with {stable_tag} then exactly {sum(EXPECTED.values())} approved breaks remain")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--against-tag", default="v7.0.2")
    arguments = parser.parse_args()
    given_v8_candidate_when_compared_then_only_approved_breaks_exist(arguments.against_tag)
