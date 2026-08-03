# Phase 1 release evidence

## Candidate

- Source branch: `develop`
- Last stable `gym-proto` tag: `v1.0.6`
- Candidate source release: `v1.1.0`
- Candidate Java artifact: `com.gym.proto:gym-proto-java:1.1.0`
- Candidate Go artifact: `github.com/pploc/proto-go@v1.1.0`
- Publication status: not published
- Human approval status: pending

## Compatibility baseline exception

Commit `660f324` on `develop` intentionally removed Member's QR-secret RPC and
moved QR rotation to Check-in after tag `v1.0.6`. Consequently, an unqualified
`buf breaking` against `v1.0.6` reports that pre-existing deletion. Phase 1 CI:

1. checks every unaffected schema against `v1.0.6`; and
2. checks `proto/member/v1/member.proto` against the exact Phase 1 base commit
   `246053eb7b2b49fb6c8875830d44a9141d210d3d` (`246053e`).

This exception does not waive semantic review and does not hide any deletion made
by Phase 1.

## Local technical verification

On 2026-08-03, the candidate passed:

- `buf format -d --exit-code proto`
- `buf lint proto`
- stable-tag compatibility for all schemas except the documented Member baseline
- incremental Member compatibility against the pre-Phase-1 commit
- clean Java, Go, gRPC, and grpc-gateway generation
- generated route assertion proving the internal Member RPCs have no HTTP routes
- `./gradlew clean check` including offline verification of all nine fixtures
- live fixture generation and read-only verification against a clean local
  Confluent Schema Registry 7.7.1
- live compatible-addition and incompatible-type-change Registry checks
- all nine generated subjects reported `BACKWARD`

Fixture SHA-256:

```text
e5a5d0944229c9e0c97dc5e872f01e7597993e5732f2014b7d8e5efdf965a27e
```

## Evidence still unavailable

These G1 requirements depend on immutable external artifacts and therefore remain
pending until an authorized tag publication runs:

- Java external-resolution smoke test for version `1.1.0`
- Go external-resolution smoke test for tag `v1.1.0` without `replace`
- published source/package/tag/checksum matrix
- accountable owner approvals

The workflow publishes only from the protected target tag and attaches source SHA,
fixture checksum, generated checksums, and release reports. This document must not
be interpreted as approval to push, tag, or publish.
