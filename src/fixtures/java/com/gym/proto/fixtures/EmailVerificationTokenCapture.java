package com.gym.proto.fixtures;

import com.gym.proto.events.v1.EmailVerificationRequestedEvent;
import io.confluent.kafka.serializers.protobuf.KafkaProtobufDeserializer;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.common.serialization.ByteArrayDeserializer;

import java.net.URI;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.PosixFilePermission;
import java.time.Duration;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/** Captures one matching verification token without logging the verification URL. */
public final class EmailVerificationTokenCapture {
    private EmailVerificationTokenCapture() {
    }

    public static void main(String[] args) {
        if (args.length == 1 && "--self-check".equals(args[0])) {
            selfCheck();
            return;
        }
        if (args.length != 5) {
            throw new IllegalArgumentException("Usage: <kafka-brokers> <schema-registry-url> <email> <timeout-seconds> <output-path>");
        }

        String brokers = args[0];
        String schemaRegistryUrl = args[1];
        String email = args[2];
        long timeoutSeconds = Long.parseLong(args[3]);
        Path outputPath = Path.of(args[4]);
        if (brokers.isBlank() || schemaRegistryUrl.isBlank() || email.isBlank() || timeoutSeconds <= 0) {
            throw new IllegalArgumentException("Kafka brokers, Schema Registry URL, email, and positive timeout are required");
        }
        if (Files.exists(outputPath)) {
            throw new IllegalArgumentException("Output path already exists");
        }
        Path parent = outputPath.getParent();
        if (parent != null) {
            try {
                Files.createDirectories(parent);
            } catch (java.io.IOException exception) {
                throw new IllegalStateException("Could not prepare token capture path", exception);
            }
        }

        Map<String, Object> properties = Map.of(
                ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, brokers,
                ConsumerConfig.GROUP_ID_CONFIG, "g5-email-capture-" + UUID.randomUUID(),
                ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest",
                ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, false,
                ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, ByteArrayDeserializer.class,
                ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, KafkaProtobufDeserializer.class,
                "schema.registry.url", schemaRegistryUrl,
                "specific.protobuf.value.type", EmailVerificationRequestedEvent.class.getName()
        );
        try (KafkaConsumer<byte[], EmailVerificationRequestedEvent> consumer = new KafkaConsumer<>(properties)) {
            consumer.subscribe(java.util.List.of("identity.email.verification-requested.v1"));
            long deadline = System.nanoTime() + Duration.ofSeconds(timeoutSeconds).toNanos();
            while (System.nanoTime() < deadline) {
                ConsumerRecords<byte[], EmailVerificationRequestedEvent> records = consumer.poll(Duration.ofMillis(500));
                for (var record : records) {
                    EmailVerificationRequestedEvent event = record.value();
                    if (event != null && email.equals(event.getEmail())) {
                        writeToken(outputPath, tokenFrom(event.getVerificationUrl()));
                        return;
                    }
                }
            }
        }
        throw new IllegalStateException("Timed out waiting for matching email verification event");
    }

    private static void selfCheck() {
        assert "raw-token".equals(tokenFrom("https://app.example.test/verify-email?unused=value&token=raw-token"));
        try {
            tokenFrom("https://app.example.test/verify-email");
            throw new AssertionError("missing token must fail");
        } catch (IllegalStateException expected) {
            // Expected.
        }
    }

    private static void writeToken(Path outputPath, String token) {
        try {
            Files.writeString(outputPath, token, StandardCharsets.UTF_8);
            try {
                Files.setPosixFilePermissions(outputPath, Set.of(
                        PosixFilePermission.OWNER_READ,
                        PosixFilePermission.OWNER_WRITE
                ));
            } catch (UnsupportedOperationException ignored) {
                // Filesystem does not support POSIX permissions.
            }
        } catch (java.io.IOException exception) {
            throw new IllegalStateException("Could not write token capture", exception);
        }
    }

    private static String tokenFrom(String verificationUrl) {
        String query = URI.create(verificationUrl).getRawQuery();
        if (query != null) {
            for (String pair : query.split("&")) {
                String[] parts = pair.split("=", 2);
                if (parts.length == 2 && "token".equals(parts[0])) {
                    String token = URLDecoder.decode(parts[1], StandardCharsets.UTF_8);
                    if (!token.isBlank()) {
                        return token;
                    }
                }
            }
        }
        throw new IllegalStateException("Verification event contains no token");
    }
}
