package com.gym.proto.fixtures;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;

/**
 * Proves Identity and Check-in fixture subjects accept a backward-compatible
 * Protobuf change and reject a backward-incompatible field type change without mutation.
 */
public final class ConfluentCompatibilityVerifier {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final CompatibilityCase[] CASES = {
            new CompatibilityCase(
                    "identity.user.registered.v1-value",
                    "    json_name = \"timestamp\"\n"
                            + "  ];\n"
                            + "}\n"
                            + "message UserSuspendedEvent {",
                    "    json_name = \"timestamp\"\n"
                            + "  ];\n"
                            + "  string fixture_note = 8 [json_name = \"fixtureNote\"];\n"
                            + "}\n"
                            + "message UserSuspendedEvent {",
                    "  string email = 2 [",
                    "  int64 email = 2 ["
            ),
            new CompatibilityCase(
                    "checkin.recorded.v1-value",
                    "    json_name = \"checkedInAt\"\n"
                            + "  ];\n"
                            + "}",
                    "    json_name = \"checkedInAt\"\n"
                            + "  ];\n"
                            + "  string fixture_note = 5 [json_name = \"fixtureNote\"];\n"
                            + "}",
                    "  string gym_id = 2 [",
                    "  int64 gym_id = 2 ["
            )
    };

    private ConfluentCompatibilityVerifier() {
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            throw new IllegalArgumentException("Usage: <schema-registry-url>");
        }

        String schemaRegistryUrl = args[0].replaceAll("/$", "");
        HttpClient client = HttpClient.newHttpClient();
        for (CompatibilityCase compatibilityCase : CASES) {
            verifyCase(client, schemaRegistryUrl, compatibilityCase);
        }
    }

    private static void verifyCase(
            HttpClient client,
            String schemaRegistryUrl,
            CompatibilityCase compatibilityCase) throws Exception {
        String subjectPath = URLEncoder.encode(compatibilityCase.subject(), StandardCharsets.UTF_8);
        JsonNode latest = getJson(client, schemaRegistryUrl + "/subjects/" + subjectPath + "/versions/latest");
        String schema = latest.path("schema").asText();
        require(!schema.isBlank(), "Fixture subject has no Protobuf schema: " + compatibilityCase.subject());
        JsonNode references = latest.path("references");

        String backwardCompatible = schema.replace(
                compatibilityCase.additiveTarget(),
                compatibilityCase.additiveReplacement()
        );
        require(!backwardCompatible.equals(schema),
                "Could not create positive compatibility candidate for " + compatibilityCase.subject());

        String backwardIncompatible = schema.replace(
                compatibilityCase.incompatibleTarget(),
                compatibilityCase.incompatibleReplacement()
        );
        require(!backwardIncompatible.equals(schema),
                "Could not create negative compatibility candidate for " + compatibilityCase.subject());

        require(isCompatible(client, schemaRegistryUrl, subjectPath, backwardCompatible, references),
                "BACKWARD compatibility rejected additive Protobuf candidate for "
                        + compatibilityCase.subject());
        require(!isCompatible(client, schemaRegistryUrl, subjectPath, backwardIncompatible, references),
                "BACKWARD compatibility accepted incompatible field type change for "
                        + compatibilityCase.subject());
    }

    private static boolean isCompatible(
            HttpClient client,
            String schemaRegistryUrl,
            String subjectPath,
            String candidate,
            JsonNode references) throws Exception {
        // Protobuf subjects import validate/common; Registry rejects candidates without refs.
        String body = JSON.writeValueAsString(
                new CompatibilityRequest(FixtureSupport.SCHEMA_TYPE, candidate, references));
        HttpRequest request = HttpRequest.newBuilder(
                        URI.create(schemaRegistryUrl + "/compatibility/subjects/" + subjectPath + "/versions/latest"))
                .header("Content-Type", "application/vnd.schemaregistry.v1+json")
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        require(response.statusCode() == 200,
                "Schema Registry compatibility request failed with HTTP " + response.statusCode());
        return JSON.readTree(response.body()).path("is_compatible").asBoolean();
    }

    private static JsonNode getJson(HttpClient client, String url) throws Exception {
        HttpResponse<String> response = client.send(
                HttpRequest.newBuilder(URI.create(url)).GET().build(),
                HttpResponse.BodyHandlers.ofString()
        );
        require(response.statusCode() == 200, "Schema Registry request failed with HTTP " + response.statusCode());
        return JSON.readTree(response.body());
    }

    private static void require(boolean condition, String message) {
        if (!condition) {
            throw new IllegalStateException(message);
        }
    }

    private record CompatibilityCase(
            String subject,
            String additiveTarget,
            String additiveReplacement,
            String incompatibleTarget,
            String incompatibleReplacement) {
    }

    private record CompatibilityRequest(String schemaType, String schema, JsonNode references) {
    }
}
