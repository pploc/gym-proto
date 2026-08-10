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
 * Proves the fixture Registry accepts a backward-compatible Protobuf change
 * and rejects a backward-incompatible field type change without mutating it.
 */
public final class ConfluentCompatibilityVerifier {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final String SUBJECT = "identity.user.registered.v1-value";

    private ConfluentCompatibilityVerifier() {
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            throw new IllegalArgumentException("Usage: <schema-registry-url>");
        }

        String schemaRegistryUrl = args[0].replaceAll("/$", "");
        HttpClient client = HttpClient.newHttpClient();
        String subjectPath = URLEncoder.encode(SUBJECT, StandardCharsets.UTF_8);
        JsonNode latest = getJson(client, schemaRegistryUrl + "/subjects/" + subjectPath + "/versions/latest");
        String schema = latest.path("schema").asText();
        require(!schema.isBlank(), "Fixture subject has no Protobuf schema");
        JsonNode references = latest.path("references");

        // UserRegisteredEvent fields are multi-line (protovalidate options). Match the
        // closed message boundary, not the pre-validate single-line form.
        String registeredClose =
                "    json_name = \"timestamp\"\n"
                        + "  ];\n"
                        + "}\n"
                        + "message UserSuspendedEvent {";
        String backwardCompatible = schema.replace(
                registeredClose,
                "    json_name = \"timestamp\"\n"
                        + "  ];\n"
                        + "  string fixture_note = 8 [json_name = \"fixtureNote\"];\n"
                        + "}\n"
                        + "message UserSuspendedEvent {"
        );
        require(!backwardCompatible.equals(schema), "Could not create positive compatibility candidate");

        String backwardIncompatible = schema.replace(
                "  string email = 2 [",
                "  int64 email = 2 ["
        );
        require(!backwardIncompatible.equals(schema), "Could not create negative compatibility candidate");

        require(isCompatible(client, schemaRegistryUrl, subjectPath, backwardCompatible, references),
                "BACKWARD compatibility rejected the additive Protobuf candidate");
        require(!isCompatible(client, schemaRegistryUrl, subjectPath, backwardIncompatible, references),
                "BACKWARD compatibility accepted the incompatible field type change");
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

    private record CompatibilityRequest(String schemaType, String schema, JsonNode references) {
    }
}
