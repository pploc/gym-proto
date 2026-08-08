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

## Published artifact verification

Publication was authorized and completed on 2026-08-03:

- `gym-proto` source tag `v1.1.0` resolves to source commit
  `740e476915117ab594a6e7ee3677e6a2c39c3c80`.
- `github.com/pploc/proto-go@v1.1.0` resolves without `replace` to commit
  `6f070d25f8361e6550e0bd9a309a738d2a0dbd21`.
- A clean Go module compiled representative Identity, Member, Payment, and
  Membership event types and found the published fixture contract.
- `com.gym.proto:gym-proto-java:1.1.0` resolved from GitHub Packages using
  consumer credentials. A clean Java 26 compilation imported representative
  Identity, Member, Payment, and Membership event classes.
- The GitHub release is available at
  `https://github.com/pploc/gym-proto/releases/tag/v1.1.0` with fixture,
  generated-output, source, and proto-go bundle evidence.

The original tag workflow published both language artifacts successfully but its
final GitHub release step failed because `release-report.json` was empty. Commit
`93cda9f` fixed the missing `jq -n` input and added recoverable evidence handling;
workflow run `30786709517` rebuilt the immutable-tag evidence and published the
release successfully without replacing either release tag.

## Human approvals still unavailable

Accountable owner approvals remain pending. Technical G1 evidence is complete, but
this document does not infer human approval or production promotion authorization.
The workflow publishes only from the protected target tag and attaches source SHA,
fixture checksum, generated checksums, and release reports.

---

# Phase 6 candidate release evidence

## Candidate

- Source branch: `develop`
- Last stable `gym-proto` tag: `v2.0.0`
- Candidate source release: `v3.0.0`
- Candidate Java artifact: `com.gym.proto:gym-proto-java:3.0.0`
- Candidate Go module: `github.com/pploc/proto-go/v3@v3.0.0`
- Publication status: not published
- Human approval status: pending

## Ownership and contract change

- Plans becomes sole owner of gym locations and membership-plan catalog.
- Member loses location and catalog RPCs and keeps profiles, purchase, lifecycle,
  membership lookup, validation, and list-by-status.
- Payment initiation gains additive `user_id` and `amount_vnd`. Membership
  `reference_id` is Member-owned `purchase_id`.
- All generated Go packages move under `github.com/pploc/proto-go/v3`.

## Expected source break against `v2.0.0`

- All `go_package` options change to the `/v3` module prefix.
- Member deletes `GetPlans` and all gym-location RPCs plus related messages.
- Plans adds public catalog and location RPCs plus internal `GetActiveGym` and
  `ResolvePurchasablePlan`.
- Payment request fields `user_id` and `amount_vnd` are additive and do not alter
  existing field numbers.

## Local technical verification

Local G6 validation on the candidate tree completed on 2026-08-08 against source
commit `f12efd0c3628db3f758b4d8f2df29929199dbfb7` plus the uncommitted G6 working
tree:

1. `buf format -d --exit-code proto`
2. `buf lint proto`
3. `buf breaking` against `v2.0.0` contained only planned `/v3` go_package moves and
   Member location/catalog symbol removals
4. `python3 scripts/verify-http-config.py`
5. clean generation and `scripts/verify-generated-routes.sh`
6. generated Java compile via `./gradlew clean compileJava compileFixturesJava`
7. temporary Go module `github.com/pploc/proto-go/v3` built with `go test ./...`
8. deterministic generation checksum comparison
9. live clean Schema Registry 7.7.1 fixture regeneration and committed-artifact match
10. `./gradlew check` including offline fixture verification
11. `./gradlew verifyConfluentBackwardCompatibility` with all ten subjects reporting
    `BACKWARD`

Generated tree aggregate SHA-256 over sorted file digests:

```text
f3d2266c241af498dc7279a358f944b9d53636218d0949caf8ac149839dd17f5
```

Fixture artifact regenerated from a disposable clean Registry (schema IDs start at 1):

```text
8a767863aa47842144729fc40d5033b3b56760dab1b51eff3ea8ca84eec310d5  contracts/v1/kafka/confluent-7.7.1-fixtures.json
```

Kafka event wire schemas remain unchanged; only clean-registry schema IDs and the
ten-subject inventory are refreshed so CI can match a disposable Registry.

## Publication and owner approval

Owner authorized tagging/publishing. First `v3.0.0` tag attempt on `7c4e194` failed
validation because the committed fixture still carried non-clean schema IDs and the
workflow hard-coded nine subjects. The failed tag is moved to the fixed candidate
commit after local fixture regeneration and subject-count correction. Existing
historical evidence above is preserved and not rewritten.
