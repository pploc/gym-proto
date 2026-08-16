# Confluent Protobuf fixture procedure

`confluent-7.7.1-fixtures.json` is a generated, committed artifact. It does not exist until it is generated from a real clean Confluent Schema Registry 7.7.1 instance. Fixture serialization uses the serializer version pinned by `build.gradle`; generated metadata records that runtime version. Do not hand-author frame bytes, schema IDs, or message-index bytes.

## Preconditions

- Confluent Schema Registry **7.7.1** is reachable over HTTP.
- The Registry is disposable and has no subjects. The generator rejects a non-empty Registry.

Start the pinned local environment when Docker is available:

```bash
docker compose -f contracts/v1/kafka/compose.confluent-7.7.1.yml up -d
until curl --fail --silent http://localhost:8081/subjects >/dev/null; do sleep 2; done
```
- The checked-out schema source is the exact candidate being released.
- The Java fixture harness compiles with the repository's Java 26 target.
- Use the repository Gradle wrapper (`./gradlew`); Gradle provisions the Java 26 toolchain when needed.

## Generate

Run against a new Registry:

```bash
./gradlew generateConfluentFixtures \
  -PschemaRegistryUrl=http://localhost:8081 \
  --no-daemon
```

The generator writes the Registry URL used for generation, but omits wall-clock
time so a clean Registry produces deterministic contract content. CI normalizes only
the environment-specific URL before comparing the generated document with the
committed artifact.

The generator:

1. sets subject compatibility to `BACKWARD`;
2. uses `TopicNameStrategy`, yielding `<topic>-value` subjects;
3. registers concrete Protobuf schemas only for this fixture-generation operation;
4. serializes every fixed `events.v1` Identity, Payment, Membership, and Check-in fixture through the exact `kafka-protobuf-serializer` version pinned by `build.gradle`;
5. records the complete Confluent frame, magic byte, big-endian Registry schema ID, Protobuf message-index bytes, raw payload, metadata, topic/key, and canonical headers.

Production clients must set `auto.register.schemas=false`. Generation is the sole controlled exception.

## Verify

After reviewing and committing the generated artifact:

```bash
./gradlew verifyConfluentFixtures --no-daemon
```

For release evidence, verify again against the seeded Registry:

```bash
./gradlew verifyConfluentFixtures \
  -PschemaRegistryUrl=http://localhost:8081 \
  --no-daemon

./gradlew verifyConfluentBackwardCompatibility \
  -PschemaRegistryUrl=http://localhost:8081 \
  --no-daemon
```

The offline verifier decodes every raw Protobuf payload, checks deterministic message fields and canonical headers, decomposes each complete frame, and ensures the encoded schema ID and message-index bytes match the artifact. With `schemaRegistryUrl`, it also checks that the live subject, schema ID, schema version, and `PROTOBUF` schema type match the generated artifact, then proves the Java `KafkaProtobufSerializer` with production `auto.register.schemas=false` reproduces each exact frame. `verifyConfluentBackwardCompatibility` uses Schema Registry's compatibility API without registering either candidate: it proves that adding an optional field succeeds and changing `email` from `string` to `int64` fails. Neither mode mutates Registry state or fixture artifacts.

## Release evidence

The release gate requires the generated artifact, command output from fixture generation and verification, a real Registry `BACKWARD` positive and negative compatibility result, Java producer/consumer fixture conformance, and a released `github.com/pploc/proto-go` tag. Keep `contracts/v1/manifest.json` pending until those facts and named approvals exist.

Stop and remove the disposable environment after capturing evidence:

```bash
docker compose -f contracts/v1/kafka/compose.confluent-7.7.1.yml down -v
```
