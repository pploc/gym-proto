package com.gym.proto.fixtures;

import io.confluent.kafka.schemaregistry.client.CachedSchemaRegistryClient;
import io.confluent.kafka.schemaregistry.client.rest.entities.Config;

import java.util.Map;

/** Registers the frozen fixture schemas in an empty disposable Schema Registry. */
public final class ConfluentSchemaSeeder {
    private ConfluentSchemaSeeder() {
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            throw new IllegalArgumentException("Usage: <schema-registry-url>");
        }

        String schemaRegistryUrl = args[0];
        CachedSchemaRegistryClient registry = new CachedSchemaRegistryClient(schemaRegistryUrl, 100);
        try {
            for (Map.Entry<String, FixtureSupport.FixtureCase> entry : FixtureSupport.cases().entrySet()) {
                FixtureSupport.FixtureCase fixture = entry.getValue();
                registry.updateConfig(fixture.subject(), new Config(FixtureSupport.COMPATIBILITY));
                FixtureSupport.serialize(fixture.topic(), fixture.message(), schemaRegistryUrl);
            }
        } finally {
            registry.close();
        }
    }
}
