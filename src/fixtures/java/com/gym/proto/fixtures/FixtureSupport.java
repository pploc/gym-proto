package com.gym.proto.fixtures;

import com.google.protobuf.Message;
import com.gym.proto.events.v1.MembershipActivatedEvent;
import com.gym.proto.events.v1.MembershipExpiredEvent;
import com.gym.proto.events.v1.MembershipExpiringSoonEvent;
import com.gym.proto.events.v1.MembershipPausedEvent;
import com.gym.proto.events.v1.MembershipResumedEvent;
import com.gym.proto.events.v1.PaymentCompletedEvent;
import com.gym.proto.events.v1.UserRegisteredEvent;
import com.gym.proto.events.v1.UserRoleChangedEvent;
import com.gym.proto.events.v1.UserSuspendedEvent;
import io.confluent.kafka.schemaregistry.client.CachedSchemaRegistryClient;
import io.confluent.kafka.serializers.protobuf.KafkaProtobufSerializer;

import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.Map;

final class FixtureSupport {
    static final String SUBJECT_NAME_STRATEGY =
            "io.confluent.kafka.serializers.subject.TopicNameStrategy";
    static final String SCHEMA_TYPE = "PROTOBUF";
    static final String COMPATIBILITY = "BACKWARD";

    private FixtureSupport() {
    }

    static Map<String, FixtureCase> cases() {
        Map<String, FixtureCase> fixtures = new LinkedHashMap<>();
        fixtures.put("user-registered", new FixtureCase(
                "identity.user.registered.v1",
                "user-001",
                "events.v1.UserRegisteredEvent",
                UserRegisteredEvent.newBuilder()
                        .setUserId("user-001")
                        .setEmail("user-001@example.test")
                        .setFullName("Fixture User")
                        .setRole("CUSTOMER")
                        .setAuthProvider("PASSWORD")
                        .setTimestamp(1_700_000_000_123L)
                        .build(),
                canonicalHeaders(
                        "events.v1.UserRegisteredEvent",
                        "ms-gym-identifier",
                        "1700000000123",
                        "fixture-user-registered-001",
                        "00-00000000000000000000000000000001-0000000000000001-01"
                )
        ));
        fixtures.put("user-suspended", new FixtureCase(
                "identity.user.suspended.v1",
                "user-002",
                "events.v1.UserSuspendedEvent",
                UserSuspendedEvent.newBuilder()
                        .setUserId("user-002")
                        .setRole("CUSTOMER")
                        .setTimestamp(1_700_000_000_456L)
                        .build(),
                canonicalHeaders(
                        "events.v1.UserSuspendedEvent",
                        "ms-gym-identifier",
                        "1700000000456",
                        "fixture-user-suspended-002",
                        "00-00000000000000000000000000000002-0000000000000002-01"
                )
        ));
        fixtures.put("user-role-changed", new FixtureCase(
                "identity.user.role-changed.v1",
                "user-003",
                "events.v1.UserRoleChangedEvent",
                UserRoleChangedEvent.newBuilder()
                        .setUserId("user-003")
                        .setOldRole("CUSTOMER")
                        .setNewRole("TRAINER")
                        .setTimestamp(1_700_000_000_789L)
                        .build(),
                canonicalHeaders(
                        "events.v1.UserRoleChangedEvent",
                        "ms-gym-identifier",
                        "1700000000789",
                        "fixture-user-role-changed-003",
                        "00-00000000000000000000000000000003-0000000000000003-01"
                )
        ));
        fixtures.put("payment-completed", new FixtureCase(
                "payment.completed.v1",
                "user-004",
                "events.v1.PaymentCompletedEvent",
                PaymentCompletedEvent.newBuilder()
                        .setPaymentId("payment-004")
                        .setUserId("user-004")
                        .setType("MEMBERSHIP")
                        .setReferenceId("plan-monthly-001")
                        .setAmountVnd(500_000L)
                        .setProvider("VNPAY")
                        .setGymId("gym-001")
                        .setDiscountApplied(true)
                        .setDiscountPercentage(10)
                        .setTimestamp(1_700_000_001_000L)
                        .build(),
                canonicalHeaders(
                        "events.v1.PaymentCompletedEvent",
                        "ms-gym-payment",
                        "1700000001000",
                        "fixture-payment-completed-004",
                        "00-00000000000000000000000000000004-0000000000000004-01"
                )
        ));
        fixtures.put("membership-activated", new FixtureCase(
                "membership.activated.v1",
                "member-005",
                "events.v1.MembershipActivatedEvent",
                MembershipActivatedEvent.newBuilder()
                        .setMemberId("member-005")
                        .setUserId("user-005")
                        .setPlanType("MONTHLY")
                        .setStartDate("2023-11-14")
                        .setEndDate("2023-12-14")
                        .setGymId("gym-001")
                        .setIsRenewal(false)
                        .setTimestamp(1_700_000_001_234L)
                        .build(),
                canonicalHeaders(
                        "events.v1.MembershipActivatedEvent",
                        "ms-gym-member",
                        "1700000001234",
                        "fixture-membership-activated-005",
                        "00-00000000000000000000000000000005-0000000000000005-01"
                )
        ));
        fixtures.put("membership-paused", new FixtureCase(
                "membership.paused.v1",
                "member-006",
                "events.v1.MembershipPausedEvent",
                MembershipPausedEvent.newBuilder()
                        .setMemberId("member-006")
                        .setPausedAt(1_700_000_001_456L)
                        .setRemainingDays(20)
                        .setGymId("gym-002")
                        .build(),
                canonicalHeaders(
                        "events.v1.MembershipPausedEvent",
                        "ms-gym-member",
                        "1700000001456",
                        "fixture-membership-paused-006",
                        "00-00000000000000000000000000000006-0000000000000006-01"
                )
        ));
        fixtures.put("membership-resumed", new FixtureCase(
                "membership.resumed.v1",
                "member-007",
                "events.v1.MembershipResumedEvent",
                MembershipResumedEvent.newBuilder()
                        .setMemberId("member-007")
                        .setNewEndDate("2023-12-31")
                        .setGymId("gym-002")
                        .build(),
                canonicalHeaders(
                        "events.v1.MembershipResumedEvent",
                        "ms-gym-member",
                        "1700000001678",
                        "fixture-membership-resumed-007",
                        "00-00000000000000000000000000000007-0000000000000007-01"
                )
        ));
        fixtures.put("membership-expiring-soon", new FixtureCase(
                "membership.expiring-soon.v1",
                "member-008",
                "events.v1.MembershipExpiringSoonEvent",
                MembershipExpiringSoonEvent.newBuilder()
                        .setMemberId("member-008")
                        .setEndDate("2023-11-21")
                        .setPlanType("YEARLY")
                        .setGymId("gym-003")
                        .build(),
                canonicalHeaders(
                        "events.v1.MembershipExpiringSoonEvent",
                        "ms-gym-member",
                        "1700000001890",
                        "fixture-membership-expiring-soon-008",
                        "00-00000000000000000000000000000008-0000000000000008-01"
                )
        ));
        fixtures.put("membership-expired", new FixtureCase(
                "membership.expired.v1",
                "member-009",
                "events.v1.MembershipExpiredEvent",
                MembershipExpiredEvent.newBuilder()
                        .setMemberId("member-009")
                        .setExpiredAt(1_700_000_002_000L)
                        .setGymId("gym-003")
                        .build(),
                canonicalHeaders(
                        "events.v1.MembershipExpiredEvent",
                        "ms-gym-member",
                        "1700000002000",
                        "fixture-membership-expired-009",
                        "00-00000000000000000000000000000009-0000000000000009-01"
                )
        ));
        return fixtures;
    }

    static Map<String, String> canonicalHeaders(
            String eventType,
            String source,
            String timestamp,
            String eventId,
            String traceparent) {
        Map<String, String> headers = new LinkedHashMap<>();
        headers.put("event-type", eventType);
        headers.put("source", source);
        headers.put("timestamp", timestamp);
        headers.put("event-id", eventId);
        headers.put("traceparent", traceparent);
        return headers;
    }

    static byte[] serialize(String topic, Message message, String schemaRegistryUrl) {
        Map<String, Object> configuration = Map.of(
                "schema.registry.url", schemaRegistryUrl,
                "value.subject.name.strategy", SUBJECT_NAME_STRATEGY,
                "auto.register.schemas", true
        );
        KafkaProtobufSerializer<Message> serializer = new KafkaProtobufSerializer<>(
                new CachedSchemaRegistryClient(schemaRegistryUrl, 100),
                configuration
        );
        try {
            return serializer.serialize(topic, message);
        } finally {
            serializer.close();
        }
    }

    static String hex(byte[] bytes) {
        return HexFormat.of().formatHex(bytes);
    }

    static byte[] fromHex(String value) {
        return HexFormat.of().parseHex(value);
    }

    record FixtureCase(
            String topic,
            String key,
            String eventType,
            Message message,
            Map<String, String> headers) {
        String subject() {
            return topic + "-value";
        }
    }
}
