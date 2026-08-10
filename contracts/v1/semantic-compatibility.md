# Semantic compatibility policy

Binary compatibility is necessary but not sufficient. Buf and Schema Registry can
accept a change that preserves wire encoding while changing the domain meaning seen
by source and JSON consumers.

## Recorded incident

In `v1.0.1`, fields named `emergency_contact` in `member.v1.MemberResponse` field 7
and `member.v1.UpdateProfileRequest` field 5 became `date_of_birth` at the same field
numbers. Both values use the Protobuf `string` wire type, so the bytes remained
parseable, but source APIs, JSON names, and domain meaning changed incompatibly.
That change is treated as a semantic contract break and must not be repeated.

## Release classification

- Adding a field or RPC without changing existing behavior requires a minor release.
- Removing or renaming a field, reusing a field number, or changing to an
  incompatible field type requires a major contract change.
- Changing a topic, required header, subject strategy, retry policy, or DLQ contract
  incompatibly requires a new contract generation and new versioned topics.
- Optional headers may be added only after confirming existing consumers ignore
  unknown headers safely.
- Java and Go artifacts must be generated from and released for the same source tag.

## Required semantic review

Every Protobuf change must answer and record the following before release:

- [ ] Existing field numbers, names, JSON names, types, cardinality, and domain
      meanings are unchanged.
- [ ] Removed field numbers and names are reserved rather than reused.
- [ ] Enum numeric values and meanings are unchanged; newly added values are handled
      safely by existing consumers.
- [ ] Existing RPC request/response meaning, authorization, and HTTP exposure are
      unchanged.
- [ ] New RPCs and fields are additive and have an explicit release classification.
- [ ] Kafka message meaning, ordering key, topic, subject, and required headers remain
      compatible.
- [ ] `buf breaking` is run against the last stable tag, and the reviewer separately
      evaluates source, JSON, and domain semantics that binary checks cannot detect.
- [ ] Generated Java and Go outputs derive from the same candidate source SHA and
      release version.

## v2.0.0 semantic review

- [x] `RegisterRequest.role` and `RegisterRequest.gym_id` are removed and reserved;
      self-registration is always a chain-wide customer registration.
- [x] `UserResponse.gym_id` and `MemberResponse.gym_id` are removed and reserved;
      identity and member profiles are chain-wide.
- [x] Identity events remove and reserve chain-wide `gym_id` fields. Gym-specific
      lifecycle events continue carrying `gym_id`.
- [x] `GetMembershipStatusByUserIdRequest.gym_id` is additive and qualifies `NONE`,
      `ACTIVE`, `PAUSED`, and `EXPIRED` for one selected gym.
- [x] `SelectGym`, email-verification RPCs, and admin HTTP routes are additive.
- [x] Removed fields make this a deliberate major contract change. Existing field
      numbers are reserved and never reused.
- [x] Kafka topics, keys, framing, headers, subject strategy, retry policy, and DLQ
      contract remain unchanged. Identity event schemas require a new clean Registry
      generation because removed fields are intentionally not BACKWARD compatible.

## v3.0.0 semantic review

- [x] Gym location and membership-plan catalog ownership relocates from
      `member.v1.MemberService` to new `plans.v1.PlansService`.
- [x] Removed Member RPCs and messages: `GetPlans`, `CreateGymLocation`,
      `UpdateGymLocation`, `ListGymLocations`, `GetGymLocation`, and their request
      and response types. No field numbers are reused.
- [x] Plans public HTTP surface owns `/api/v1/gyms` and `/api/v1/plans` routes.
      Plans internal RPCs `GetActiveGym` and `ResolvePurchasablePlan` have no HTTP
      mapping and no Kong route.
- [x] Workload callers are exact: Identifier may call only Plans `GetActiveGym`;
      Member may call only Plans `ResolvePurchasablePlan`; Identifier may call only
      Member `GetMembershipStatusByUserId`.
- [x] Membership Payment initiation is additive only: `InitiatePaymentRequest`
      gains `user_id = 6` and `amount_vnd = 7`. Membership `reference_id` now means
      Member-owned `purchase_id`; trainer booking remains `booking_id`.
- [x] Frozen `PaymentCompletedEvent` field numbers and names are unchanged.
- [x] All Protobuf `go_package` options move under `github.com/pploc/proto-go/v3`.
      Protobuf API packages remain `*.v1`. Generated Go consumers must import the
      `/v3` module path.
- [x] Plans V1 has no Kafka producer, consumer, topic, outbox, or Schema Registry
      dependency. Released nine-topic Kafka inventory is unchanged.
- [x] This is a deliberate major source break. Immutable `v2.0.0` artifacts remain
      the previous stable baseline and must not be rewritten.

## v4.0.0 semantic review

Breaking cleanup of existing `*.v1` packages in place. Artifact major version is `v4.0.0`.

- [x] Buf STANDARD lint with no RPC name/uniqueness exceptions.
- [x] All RPCs use unique exact `<RpcName>Request` / `<RpcName>Response` messages.
- [x] All `google.protobuf.Empty` usages replaced with method-specific empty messages.
- [x] Shared response messages split by copying top-level fields (no wrapper nesting).
- [x] Closed vocabularies converted to proto3 enums with `*_UNSPECIFIED = 0`.
- [x] Open vocabularies (payment provider, specialties, free-text) remain strings.
- [x] Protovalidate annotations on all RPC requests and Kafka events.
- [x] Generated Go module path moves to `github.com/pploc/proto-go`.
- [x] Protobuf/Java packages remain `*.v1`.
- [x] Enum-break Kafka events move to new `.v2` topics/subjects; non-enum events stay on current generation.
- [x] HTTP selectors, verbs, paths, and body bindings preserved; internal RPCs remain unbound.

## v5.0.0 semantic review

Stage 0 is one coordinated pre-production break before Phase 9 gateway generation.

- [x] Identity `SelectGym` RPC and request/response messages are retired; their exact
      names are rejected by a source and generated-output compatibility check.
- [x] Member `GetMembershipStatusByUserId` RPC and request/response messages are
      retired; their exact names are rejected by the same compatibility check.
- [x] Access tokens carry only stable identity and token-control claims. `gym_id` and
      `membership_status` are forbidden.
- [x] Gym-specific public Member requests carry explicit validated `gym_id`; purchase
      uses nested `PurchaseMembershipBody` without losing existing inputs.
- [x] Final Member and Plans verbs, paths, body selectors, and authorization policies
      are frozen in `contracts/v1/routes.json` before Stage 1 annotations/OpenAPI.
- [x] Internal Member and Plans workload methods remain unbound.
- [x] Java and Go artifacts must be published from one source SHA as Java `5.0.0`
      and Go `v1.5.0`; existing immutable artifacts remain unchanged.
