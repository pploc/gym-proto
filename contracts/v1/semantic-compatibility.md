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
