package com.gym.proto.fixtures;

import com.google.protobuf.Message;
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
                "identity-user-1",
                "events.v1.UserRegisteredEvent",
                UserRegisteredEvent.newBuilder()
                        .setUserId("user-001")
                        .setEmail("user-001@example.test")
                        .setFullName("Fixture User")
                        .setRole("MEMBER")
                        .setGymId("gym-001")
                        .setAuthProvider("PASSWORD")
                        .setTimestamp(1_700_000_000_123L)
                        .build(),
                canonicalHeaders(
                        "events.v1.UserRegisteredEvent",
                        "identity-service",
                        "1700000000123",
                        "fixture-user-registered-001"
                )
        ));
        fixtures.put("user-suspended", new FixtureCase(
                "identity.user.suspended.v1",
                "identity-user-2",
                "events.v1.UserSuspendedEvent",
                UserSuspendedEvent.newBuilder()
                        .setUserId("user-002")
                        .setRole("MEMBER")
                        .setGymId("gym-001")
                        .setTimestamp(1_700_000_000_456L)
                        .build(),
                canonicalHeaders(
                        "events.v1.UserSuspendedEvent",
                        "identity-service",
                        "1700000000456",
                        "fixture-user-suspended-002"
                )
        ));
        fixtures.put("user-role-changed", new FixtureCase(
                "identity.user.role-changed.v1",
                "identity-user-3",
                "events.v1.UserRoleChangedEvent",
                UserRoleChangedEvent.newBuilder()
                        .setUserId("user-003")
                        .setOldRole("MEMBER")
                        .setNewRole("TRAINER")
                        .setGymId("gym-002")
                        .setTimestamp(1_700_000_000_789L)
                        .build(),
                canonicalHeaders(
                        "events.v1.UserRoleChangedEvent",
                        "identity-service",
                        "1700000000789",
                        "fixture-user-role-changed-003"
                )
        ));
        return fixtures;
    }

    static Map<String, String> canonicalHeaders(
            String eventType,
            String source,
            String timestamp,
            String eventId) {
        Map<String, String> headers = new LinkedHashMap<>();
        headers.put("event-type", eventType);
        headers.put("source", source);
        headers.put("timestamp", timestamp);
        headers.put("event-id", eventId);
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
