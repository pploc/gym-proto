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
workflow hard-coded nine subjects. The failed tag was moved to the fixed candidate
commit after local fixture regeneration and subject-count correction.

Publication completed on 2026-08-08 from workflow run `31258506342`:

- Source tag `v3.0.0` resolves to commit `ea00953ca803a12741d6d1ca1f45ab4cadac66a8`.
- GitHub release: `https://github.com/pploc/gym-proto/releases/tag/v3.0.0`
- Fixture SHA-256: `8a767863aa47842144729fc40d5033b3b56760dab1b51eff3ea8ca84eec310d5`
- Generated tree aggregate SHA-256: `f3d2266c241af498dc7279a358f944b9d53636218d0949caf8ac149839dd17f5`
- `github.com/pploc/proto-go/v3@v3.0.0` resolves without `replace` to commit
  `4e88408e271c430e5cdbe19a4bf2652c6e935171` and includes `plans/v1`.
- `com.gym.proto:gym-proto-java:3.0.0` resolves from GitHub Packages.

Existing historical evidence above is preserved and not rewritten.

---

# Phase 10 candidate release evidence

## Candidate

- Source branch: `develop`
- Last stable `gym-proto` tag: `v6.0.1`
- Candidate source release: `v7.0.0`
- Candidate Java artifact: `com.gym.proto:gym-proto-java:7.0.0`
- Candidate Go artifact: `github.com/pploc/proto-go@v1.7.0`
- Publication status: not published
- Human approval status: pending

## Coordinated G10 contract change

- Check-in exposes exactly six JWT-authenticated public RPCs with customer identity
  derived from verified `sub`; self-history and administrator history are separate.
- Display-device registration, credentials, revocation, and `device_id` are retired.
  Logged-in `SUPER_ADMIN` display retrieval carries explicit `gym_id` as resource
  context only.
- Member `ValidateMembership` accepts `user_id` plus `gym_id` and returns canonical
  `member_id`; Plans adds Check-in-only `ValidateCheckInGym`. Both remain workload-only.
- Check-in timestamps use `google.protobuf.Timestamp`; removed field numbers and names
  remain reserved.
- `checkin.recorded.v1` uses canonical member ID as key and
  `events.v1.CheckInRecordedEvent` with TopicNameStrategy, canonical headers, and
  lookup-only production schema registration.

## Expected source break against `v6.0.1`

`scripts/verify-expected-breaking.py` requires exactly 24 approved Buf FILE
violations: retired Check-in RPCs/messages, removed and reserved member/device fields,
typed Check-in timestamps, and Member's user-based validation request. Any missing or
additional diagnostic fails validation.

## Stage 0 evidence status

Passed locally on 2026-08-16:

- Protobuf format and STANDARD lint;
- exact 24-diagnostic approved break check against immutable `v6.0.1`;
- 33-operation inline HTTP allowlist with no external YAML duplicate;
- clean generation of 702 Java, Go, gRPC, and grpc-gateway files;
- generated route and retired-symbol checks, including six exact Check-in routes and
  workload-only Member/Plans methods absent from public output;
- deterministic service and canonical OpenAPI generation with Identity 12, Member 7,
  Plans 8, Check-in 6, and 33 total operations;
- deterministic `kong-proto-7.0.0.tar.gz` packaging and Kong 3.8 startup smoke;
- known Kong source-transcoding probe reproduced the recorded `buf/validate` parser
  incompatibility for Member, Plans, and Check-in, preserving the generated-gateway
  fallback;
- generated Java and fixture-harness compilation on Java 26;
- clean Confluent Schema Registry 7.7.1 generation of all eleven fixtures using
  `kafka-protobuf-serializer:8.0.7`;
- offline and live fixture verification, lookup-only serializer conformance, and live
  BACKWARD additive/incompatible-type checks for Identity and the new Check-in subject;
- full `./gradlew check --no-daemon`;
- deterministic generation checksums, JSON/YAML and Python/shell syntax checks,
  whitespace checks, and Gnostic `v0.7.1` source commit verification.

Generated Kafka fixture artifact:

```text
e79341b996d5052c0e0e4a0fe2621fd5edab6ad3b2d3a8304678664cbb46b4ab  contracts/v1/kafka/confluent-7.7.1-fixtures.json
```

### Gate 1 validation status

Actions run [`31930988141`](https://github.com/pploc/gym-proto/actions/runs/31930988141)
passed on 2026-08-16 for source SHA
`80950af313306491029b8eff464698678fdda9ba`. It was an unprotected `develop`
validation run, not protected CI or release evidence. Publication was correctly
skipped because the ref was not `refs/tags/v7.0.0`.

Its `gym-proto-validation-80950af313306491029b8eff464698678fdda9ba` artifact
contained an empty `validation-report.json`: the validation workflow omitted
`jq -n` when writing the report. That artifact is not valid Gate 1 report
evidence. The repair requires a fresh validation run on a new source SHA.

`develop` has no branch protection or ruleset, and the `release` environment has
no required reviewer or deployment-branch restriction. Those missing protections
remain a release blocker and must not be relabeled as protected CI.

`verify-kong-errors.py --release` validates the committed G9 generated-gateway
and Kong error-evidence contract. This validation run did not perform a fresh G10
Stage 3 Check-in route, header, or error probe; that runtime work remains pending.

Pending before publication:

- a fresh unprotected validation run on the report-repair source SHA with a
  non-empty report;
- configured and verified protection before any protected-release gate can pass;
- external Java `7.0.0` and Go `v1.7.0` resolution, which cannot exist before
  publication;
- accountable-owner approval.

No tag, package, GitHub release, runtime implementation, protected-CI result,
external artifact resolution, or owner acceptance is claimed here.
