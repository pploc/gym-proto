package com.gym.proto.fixtures;

import com.google.protobuf.Message;
import io.confluent.kafka.schemaregistry.client.CachedSchemaRegistryClient;
import io.confluent.kafka.schemaregistry.client.SchemaMetadata;
import io.confluent.kafka.schemaregistry.client.rest.entities.Config;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

public final class ConfluentFixtureGenerator {
    private ConfluentFixtureGenerator() {
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 2) {
            throw new IllegalArgumentException("Usage: <output-path> <schema-registry-url>");
        }

        FixtureSupport.requireSchemaRegistryClientVersion();
        Path outputPath = Path.of(args[0]);
        String schemaRegistryUrl = args[1];
        CachedSchemaRegistryClient registry = new CachedSchemaRegistryClient(schemaRegistryUrl, 100);
        Map<String, FixtureSupport.FixtureCase> cases = FixtureSupport.cases();
        try {
            requireCleanRegistry(registry);
            for (FixtureSupport.FixtureCase fixture : cases.values()) {
                Config config = new Config(FixtureSupport.COMPATIBILITY);
                registry.updateConfig(fixture.subject(), config);
            }

            StringBuilder casesJson = new StringBuilder();
            for (Map.Entry<String, FixtureSupport.FixtureCase> entry : cases.entrySet()) {
                if (!casesJson.isEmpty()) {
                    casesJson.append(",\n");
                }
                casesJson.append(generateCase(entry.getKey(), entry.getValue(), registry, schemaRegistryUrl));
            }
            String output = """
                    {
                      "fixtureFormatVersion": 1,
                      "generatedBy": {
                        "tool": "gym-proto ConfluentFixtureGenerator",
                        "schemaRegistryClient": "%s",
                        "schemaRegistryUrl": "%s"
                      },
                      "environment": {
                        "requireCleanRegistry": true,
                        "schemaType": "%s",
                        "subjectNameStrategy": "TopicNameStrategy",
                        "compatibility": "%s",
                        "registrationMode": "fixture-generation-only"
                      },
                      "cases": [
                    %s
                      ]
                    }
                    """.formatted(
                    FixtureSupport.SCHEMA_REGISTRY_CLIENT_VERSION,
                    escape(schemaRegistryUrl),
                    FixtureSupport.SCHEMA_TYPE,
                    FixtureSupport.COMPATIBILITY,
                    casesJson.toString()
            );
            Files.createDirectories(outputPath.getParent());
            Files.writeString(outputPath, output);
        } finally {
            registry.close();
        }
    }

    private static String generateCase(
            String name,
            FixtureSupport.FixtureCase fixture,
            CachedSchemaRegistryClient registry,
            String schemaRegistryUrl) throws Exception {
        byte[] frame = FixtureSupport.serialize(fixture.topic(), fixture.message(), schemaRegistryUrl);
        if (frame.length < 6 || frame[0] != 0) {
            throw new IllegalStateException("Serializer did not emit a Confluent Protobuf frame for " + name);
        }

        SchemaMetadata metadata = registry.getLatestSchemaMetadata(fixture.subject());
        int frameSchemaId = readSchemaId(frame);
        if (metadata.getId() != frameSchemaId) {
            throw new IllegalStateException("Frame schema ID does not match Registry subject " + fixture.subject());
        }
        if (!FixtureSupport.SCHEMA_TYPE.equals(metadata.getSchemaType())) {
            throw new IllegalStateException("Registry schema type is not PROTOBUF for " + fixture.subject());
        }

        byte[] payload = fixture.message().toByteArray();
        String payloadHex = FixtureSupport.hex(payload);
        String frameHex = FixtureSupport.hex(frame);
        String schemaIdHex = FixtureSupport.hex(new byte[]{frame[1], frame[2], frame[3], frame[4]});
        String indexHex = FixtureSupport.hex(
                slice(frame, 5, frame.length - 5 - payload.length)
        );
        String headers = fixture.headers().entrySet().stream()
                .map(header -> "          \"%s\": \"%s\"".formatted(
                        escape(header.getKey()), escape(header.getValue())))
                .collect(Collectors.joining(",\n"));

        return """
                            {
                              "name": "%s",
                              "topic": "%s",
                              "keyUtf8": "%s",
                              "subject": "%s",
                              "eventType": "%s",
                              "schema": {
                                "id": %d,
                                "version": %d,
                                "type": "%s"
                              },
                              "headers": {
                    %s
                              },
                              "payloadHex": "%s",
                              "frame": {
                                "magicByteHex": "00",
                                "schemaIdBigEndianHex": "%s",
                                "messageIndexesHex": "%s",
                                "completeHex": "%s"
                              }
                            }""".formatted(
                escape(name),
                escape(fixture.topic()),
                escape(fixture.key()),
                escape(fixture.subject()),
                escape(fixture.eventType()),
                metadata.getId(),
                metadata.getVersion(),
                FixtureSupport.SCHEMA_TYPE,
                headers,
                payloadHex,
                schemaIdHex,
                indexHex,
                frameHex
        );
    }

    private static void requireCleanRegistry(CachedSchemaRegistryClient registry) throws Exception {
        List<String> subjects = registry.getAllSubjects().stream().toList();
        if (!subjects.isEmpty()) {
            throw new IllegalStateException(
                    "Fixture generation requires a clean Registry; found subjects: " + String.join(", ", subjects)
            );
        }
    }

    private static int readSchemaId(byte[] frame) {
        return ((frame[1] & 0xff) << 24)
                | ((frame[2] & 0xff) << 16)
                | ((frame[3] & 0xff) << 8)
                | (frame[4] & 0xff);
    }

    private static byte[] slice(byte[] bytes, int start, int length) {
        Objects.checkFromIndexSize(start, length, bytes.length);
        byte[] result = new byte[length];
        System.arraycopy(bytes, start, result, 0, length);
        return result;
    }

    private static String escape(String value) {
        return value.replace("\\", "\\\\").replace("\"", "\\\"");
    }
}
