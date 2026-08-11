#!/usr/bin/env python3
"""Keep unmeasured Kong error behavior out of releases."""

import argparse
from pathlib import Path

import yaml


ERRORS = Path(__file__).resolve().parents[1] / "contracts/v1/http/kong-3.8-errors.yaml"


def given_pending_kong_measurement_when_checked_then_block_only_release() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", action="store_true")
    release = parser.parse_args().release
    document = yaml.safe_load(ERRORS.read_text())
    if document.get("kong", {}).get("version") != 3.8:
        raise SystemExit("Kong error evidence must target Kong 3.8")
    pending = document.get("measurement", {}).get("status") == "pending-stage-3-compatibility-spike"
    if document.get("release_ready") is not False or not pending:
        raise SystemExit("Kong error evidence must explicitly record pending Stage 3 measurement")
    if release:
        raise SystemExit("release blocked: Kong 3.8 error measurement remains pending")
    print("given pending Kong 3.8 error evidence when candidate is checked then release remains blocked")


if __name__ == "__main__":
    given_pending_kong_measurement_when_checked_then_block_only_release()
