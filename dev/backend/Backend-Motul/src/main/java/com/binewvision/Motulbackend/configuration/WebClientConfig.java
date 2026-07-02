

package com.binewvision.Motulbackend.configuration;


// ─────────────────────────────────────────────────────────────────────────────
// WebClientConfig.java
// ─────────────────────────────────────────────────────────────────────────────

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
public class WebClientConfig {

    /**
     * Bean WebClient partagé, utilisé par DocumentService pour appeler Python.
     * Timeout configurables via application.properties si nécessaire.
     */
    @Bean
    public WebClient webClient() {
        return WebClient.builder()
                .codecs(c -> c.defaultCodecs().maxInMemorySize(10 * 1024 * 1024))  // 10 MB
                .build();
    }
}