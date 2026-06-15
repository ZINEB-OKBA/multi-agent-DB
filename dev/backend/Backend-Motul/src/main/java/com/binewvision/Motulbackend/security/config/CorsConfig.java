package com.binewvision.Motulbackend.security.config;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;

import java.util.List;

@Configuration
public class CorsConfig implements CorsConfigurationSource {

    @Override
    public CorsConfiguration getCorsConfiguration(HttpServletRequest request) {
        CorsConfiguration config = new CorsConfiguration();

        // 🎯 1. Au lieu de "*", on nomme explicitement l'URL de ton Angular pour valider les Credentials
        config.setAllowedOrigins(List.of("http://localhost:4200", "http://127.0.0.1:4200"));

        // 🎯 2. On liste explicitement les méthodes acceptées (OPTIONS est obligatoire pour le Preflight !)
        config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "OPTIONS"));

        // 🎯 3. On autorise tous les en-têtes de requêtes entrants
        config.setAllowedHeaders(List.of("*"));

        // 🎯 4. Autorise l'envoi de cookies, tokens ou headers d'authentification
        config.setAllowCredentials(true);

        // 🎯 5. Crucial pour le téléchargement : permet à Angular de lire le nom du fichier envoyé par Spring
        config.setExposedHeaders(List.of("Content-Disposition", "Content-Type", "Content-Length"));
        return config;
    }
}