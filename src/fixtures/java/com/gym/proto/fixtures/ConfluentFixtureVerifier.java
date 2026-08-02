package com.gym.proto.fixtures;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.protobuf.Message;
import io.confluent.kafka.schemaregistry.client.CachedSchemaRegistryClient;
import io.confluent.kafka.schemaregistry.client.SchemaMetadata;
import io.confluent.kafka.serializers.protobuf.KafkaProtobufSerializer;

import java.nio.file.Path;
import java.util.Arrays;
import java.util.Iterator;
import java.util.Map;

public final class ConfluentFixtureVerifier {
    private static final ObjectMapper JSON = new ObjectMapper();

    private ConfluentFixtureVerifier() {
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 1 || args.length > 2) {
            throw new IllegalArgumentException("Usage: <fixture-path> [schema-registry-url]");
        }

        JsonNode document = JSON.readTree(Path.of(args[0]).toFile());
        String schemaRegistryUrl = args.length == 2 ? args[1] : null;
        require(document.path("fixtureFormatVersion").asInt() == 1, "Unsupported fixture format version");
        require(FixtureSupport.COMPATIBILITY.equals(document.path("environment").path("compatibility").asText()),
                "Fixture compatibility must be BACKWARD");
        require("TopicNameStrategy".equals(document.path("environment").path("subjectNameStrategy").asText()),
                "Fixture subject strategy must be TopicNameStrategy");

        Map<String, FixtureSupport.FixtureCase> expectedCases = FixtureSupport.cases();
        JsonNode fixtureCases = document.path("cases");
        require(fixtureCases.isArray(), "Fixture cases must be an array");
        require(fixtureCases.size() == expectedCases.size(), "Fixture case count does not match the contract");

        for (JsonNode fixture : fixtureCases) {
            String name = fixture.path("name").asText();
            FixtureSupport.FixtureCase expected = expectedCases.remove(name);
            require(expected != null, "Unknown fixture case: " + name);
            verifyCase(fixture, expected, schemaRegistryUrl);
        }
        require(expectedCases.isEmpty(), "Missing fixture cases: " + expectedCases.keySet());
    }

    private static void verifyCase(
            JsonNode fixture,
            FixtureSupport.FixtureCase expected,
            String schemaRegistryUrl) throws Exception {
        require(expected.topic().equals(fixture.path("topic").asText()), "Unexpected fixture topic");
        require(expected.key().equals(fixture.path("keyUtf8").asText()), "Unexpected fixture key");
        require(expected.subject().equals(fixture.path("subject").asText()), "Unexpected fixture subject");
        require(expected.eventType().equals(fixture.path("eventType").asText()), "Unexpected event type");
        require(FixtureSupport.SCHEMA_TYPE.equals(fixture.path("schema").path("type").asText()),
                "Fixture schema type must be PROTOBUF");
        require(fixture.path("schema").path("id").asInt() > 0, "Fixture schema ID must be positive");
        require(fixture.path("schema").path("version").asInt() > 0, "Fixture schema version must be positive");

        Iterator<Map.Entry<String, String>> expectedHeaders = expected.headers().entrySet().iterator();
        while (expectedHeaders.hasNext()) {
            Map.Entry<String, String> header = expectedHeaders.next();
            require(header.getValue().equals(fixture.path("headers").path(header.getKey()).asText()),
                    "Unexpected canonical header: " + header.getKey());
        }
        require(fixture.path("headers").size() == expected.headers().size(), "Unexpected fixture headers");

        byte[] payload = FixtureSupport.fromHex(fixture.path("payloadHex").asText());
        Message parsed = parse(expected.message(), payload);
        require(expected.message().equals(parsed), "Fixture payload does not decode to the expected Protobuf message");

        JsonNode frame = fixture.path("frame");
        require("00".equals(frame.path("magicByteHex").asText()), "Fixture magic byte must be 00");
        byte[] completeFrame = FixtureSupport.fromHex(frame.path("completeHex").asText());
        require(completeFrame.length >= 6, "Fixture frame is too short");
        require(completeFrame[0] == 0, "Fixture frame magic byte is invalid");
        require(Arrays.equals(payload, Arrays.copyOfRange(completeFrame, completeFrame.length - payload.length, completeFrame.length)),
                "Fixture frame payload does not match payloadHex");
        require(FixtureSupport.hex(Arrays.copyOfRange(completeFrame, 1, 5))
                        .equals(frame.path("schemaIdBigEndianHex").asText()),
                "Fixture schema ID bytes do not match complete frame");
        require(FixtureSupport.hex(Arrays.copyOfRange(completeFrame, 5, completeFrame.length - payload.length))
                        .equals(frame.path("messageIndexesHex").asText()),
                "Fixture message-index bytes do not match complete frame");
        require(readSchemaId(completeFrame) == fixture.path("schema").path("id").asInt(),
                "Fixture schema ID bytes do not match schema metadata");
        if (schemaRegistryUrl != null) {
            verifyRegistryMetadata(fixture, expected, schemaRegistryUrl);
            verifyJavaSerializerConformance(expected, completeFrame, schemaRegistryUrl);
        }
    }

    private static void verifyJavaSerializerConformance(
            FixtureSupport.FixtureCase expected,
            byte[] completeFrame,
            String schemaRegistryUrl) {
        Map<String, Object> configuration = Map.of(
                "schema.registry.url", schemaRegistryUrl,
                "value.subject.name.strategy", FixtureSupport.SUBJECT_NAME_STRATEGY,
                "auto.register.schemas", false
        );
        CachedSchemaRegistryClient registry = new CachedSchemaRegistryClient(schemaRegistryUrl, 100);
        KafkaProtobufSerializer<Message> serializer = new KafkaProtobufSerializer<>(registry, configuration);
        try {
            require(Arrays.equals(completeFrame, serializer.serialize(expected.topic(), expected.message())),
                    "Java Protobuf serializer did not reproduce the fixture frame for " + expected.topic());
        } finally {
            serializer.close();
            try {
                registry.close();
            } catch (Exception exception) {
                throw new IllegalStateException("Could not close Schema Registry client", exception);
            }
        }
    }

    private static void verifyRegistryMetadata(
            JsonNode fixture,
            FixtureSupport.FixtureCase expected,
            String schemaRegistryUrl) throws Exception {
        CachedSchemaRegistryClient registry = new CachedSchemaRegistryClient(schemaRegistryUrl, 100);
        try {
            SchemaMetadata metadata = registry.getLatestSchemaMetadata(expected.subject());
            require(metadata.getId() == fixture.path("schema").path("id").asInt(),
                    "Registry schema ID differs from fixture for " + expected.subject());
            require(metadata.getVersion() == fixture.path("schema").path("version").asInt(),
                    "Registry schema version differs from fixture for " + expected.subject());
            require(FixtureSupport.SCHEMA_TYPE.equals(metadata.getSchemaType()),
                    "Registry schema type differs from fixture for " + expected.subject());
            require(expected.subject().equals(fixture.path("subject").asText()),
                    "Registry subject differs from fixture");
        } finally {
            registry.close();
        }
    }

    private static Message parse(Message message, byte[] payload) throws Exception {
        return message.getParserForType().parseFrom(payload);
    }

    private static int readSchemaId(byte[] frame) {
        return ((frame[1] & 0xff) << 24)
                | ((frame[2] & 0xff) << 16)
                | ((frame[3] & 0xff) << 8)
                | (frame[4] & 0xff);
    }

    private static void require(boolean condition, String message) {
        if (!condition) {
            throw new IllegalStateException(message);
        }
    }
}
