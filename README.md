# Kotlin + Spring Backend Skills

A code-free catalog of agent skills for Kotlin + Spring Boot backend development.
Each skill is a self-contained `skills/<name>/SKILL.md` that the agent picks up by its description
or that you invoke by name.

Original source: <https://github.com/yalishevant/kotlin-backend-agent-skills>

## Skills

### Build and dependencies

| Skill | What it does |
|---|---|
| `gradle-kotlin-dsl-doctor` | Generate, debug and repair `build.gradle.kts` / `settings.gradle.kts` with minimal compatible changes |
| `dependency-conflict-resolver` | Diagnose classpath conflicts, version drift and BOM-vs-explicit-version issues |
| `upgrade-breaking-change-navigator` | Plan Spring Boot, Kotlin, Gradle, JDK and `javax` → `jakarta` upgrades step by step |
| `ci-cd-containerization-advisor` | Reproducible CI, layered container images, rollout safety |

### Spring core and Kotlin

| Skill | What it does |
|---|---|
| `project-context-ingestion` | Build a working model of an unfamiliar Kotlin + Spring repository |
| `spring-context-di-reasoning` | Explain bean wiring, auto-configuration and context startup failures |
| `kotlin-spring-proxy-compatibility` | Final classes, `open`/`allopen`, AOP and proxy pitfalls in Kotlin |
| `configuration-properties-profiles-kotlin-safe` | Typed `@ConfigurationProperties`, profiles and environment overrides |
| `kotlin-idiomatic-refactorer-spring-aware` | Idiomatic Kotlin refactoring that keeps Spring semantics intact |
| `java-kotlin-migration-assistant` | Behavior-preserving Java → Kotlin migration |

### API, data and integrations

| Skill | What it does |
|---|---|
| `domain-decomposition-api-design-advisor` | Bounded contexts, service boundaries and API contracts before implementation |
| `spring-mvc-webflux-api-builder` | Build HTTP APIs with Spring MVC or WebFlux |
| `error-model-validation-architect` | Consistent validation and error payloads, `@ControllerAdvice` |
| `jackson-kotlin-serialization-specialist` | Kotlin + Jackson DTOs, nullability, polymorphism, PATCH semantics |
| `jpa-spring-data-kotlin-mapper` | JPA entities and Spring Data repositories in Kotlin |
| `transaction-consistency-designer` | `@Transactional` boundaries, propagation, idempotency, locking |
| `schema-migration-planner` | Safe Flyway/Liquibase schema migrations |
| `integration-resilience-engineer` | Timeouts, retries, circuit breakers, DLQ and idempotent consumers |
| `spring-security-configurator-auditor` | Configure and audit Spring Security |

### Quality and operations

| Skill | What it does |
|---|---|
| `test-suite-builder` | Layered unit, slice and integration tests with MockK and coroutines |
| `spring-kotlin-code-review` | Review Kotlin + Spring code for correctness and framework pitfalls |
| `performance-concurrency-advisor` | Performance, coroutines, thread pools and concurrency issues |
| `observability-integrator` | Logging, metrics and tracing with Micrometer and OpenTelemetry |
| `stacktrace-log-triage` | Separate root cause from wrapper exceptions in stack traces and logs |
| `production-incident-responder` | Structured mitigation and root-cause analysis for production incidents |

## Layout

```text
plugin.json
skills/
  <skill-name>/
    SKILL.md
```

## License

MIT, see [LICENSE](LICENSE).
