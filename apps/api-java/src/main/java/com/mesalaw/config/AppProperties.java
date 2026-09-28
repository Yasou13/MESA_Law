package com.mesalaw.config;

import java.util.List;

import org.springframework.boot.context.properties.ConfigurationProperties;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.Setter;

/**
 * Type-safe configuration properties bound to the {@code mesa-law.*} prefix in
 * {@code application.yml}. This replaces the Python {@code core/config.py Settings} class.
 */
@ConfigurationProperties(prefix = "mesa-law")
@Getter
@Setter
public class AppProperties {

    @NotBlank
    private String environment = "development";

    @NotBlank
    private String secretKey = "MUST_BE_PROVIDED_IN_ENV";

    private boolean testAuthEnabled = false;
    private boolean observabilityEnabled = false;

    // ── CORS ──
    private Cors cors = new Cors();

    // ── Keycloak ──
    private Keycloak keycloak = new Keycloak();

    // ── Storage (S3 / MinIO) ──
    private Storage storage = new Storage();

    // ── Intelligence / MESA Core ──
    private Intelligence intelligence = new Intelligence();

    // ── LLM ──
    private Llm llm = new Llm();

    // ── ClamAV ──
    private Clamav clamav = new Clamav();

    // ── Feature Flags ──
    private Features features = new Features();

    // ── Worker ──
    private Worker worker = new Worker();

    /**
     * Returns true if the environment is considered secure (production, staging, pilot).
     * Matches Python's {@code Settings.is_secure_environment}.
     */
    public boolean isSecureEnvironment() {
        String env = this.environment.toLowerCase();
        return env.equals("production") || env.equals("staging") || env.equals("pilot");
    }

    /**
     * Convenience delegate to {@code features.externalResearchEnabled}.
     * Used by ResearchController.
     */
    public boolean isExternalResearchEnabled() {
        return features.isExternalResearchEnabled();
    }

    // ── Nested config classes ──

    @Getter
    @Setter
    public static class Cors {
        private List<String> allowedOrigins = List.of("http://localhost:3000", "http://127.0.0.1:3000");
    }

    @Getter
    @Setter
    public static class Keycloak {
        private String clientId = "mesa-client";
        private String clientSecret = "";
        private String issuer = "http://localhost:8080/realms/mesa_law";
        private String jwksUrl = "http://localhost:8080/realms/mesa_law/protocol/openid-connect/certs";
        private String internalUrl;
    }

    @Getter
    @Setter
    public static class Storage {
        private String endpoint = "http://localhost:9000";
        private String accessKey = "";
        private String secretKey = "";
        private String bucket = "mesa-law-docs";
        private int uploadUrlTtlSeconds = 600;
        private int downloadUrlTtlSeconds = 300;
    }

    @Getter
    @Setter
    public static class Intelligence {
        private String adapter = "mock";
        private String mesaApiKey = "";
        private String mesaBackendUrl = "http://localhost:8000";
    }

    @Getter
    @Setter
    public static class Llm {
        private String provider = "mock";
        private String model = "";
        private String apiKey = "";
        private String baseUrl = "";
        private int maxTokens = 4096;
        private double temperature = 0.1;
        private int timeoutSeconds = 60;
    }

    @Getter
    @Setter
    public static class Clamav {
        private String host = "clamav";
        private int port = 3310;
        private boolean required = true;
    }

    @Getter
    @Setter
    public static class Features {
        private boolean mesaRebuildEnabled = false;
        private boolean externalResearchEnabled = false;
        private boolean draftingAiEnabled = false;
        private boolean deadlineAiEnabled = false;
    }

    @Getter
    @Setter
    public static class Worker {
        private int concurrency = 1;
        private int leaseMinutes = 5;
    }
}
