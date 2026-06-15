package com.binewvision.Motulbackend.security.config;

import com.binewvision.Motulbackend.security.jwt.AuthEntryPointJwt;
import com.binewvision.Motulbackend.security.jwt.JwtAuthenticationFilter;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.http.HttpMethod;

import java.util.ArrayList;
import java.util.List;

@Configuration
@EnableWebSecurity
@RequiredArgsConstructor
@EnableMethodSecurity
public class SecurityConfiguration {

    private final JwtAuthenticationFilter jwtAuthFilter;
    private final AuthenticationProvider authenticationProvider;
    private final AuthEntryPointJwt unauthorizedHandler;
    private final CorsConfig corsConfig;

    protected static List<String> getWhitelist() {
        List<String> whitelist = new ArrayList<>();
        whitelist.add("/auth/authenticate");
        whitelist.add("/auth/refresh");        // ← sans /api/
        whitelist.add("/auth/new-password");
        whitelist.add("/auth/forgot-password");
        whitelist.add("/actuator/**");
        whitelist.add("/error");
        return whitelist;
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        // 1. Gestion des CORS et désactivation du CSRF (Configuré via ta classe CorsConfig)
        http.cors(cors -> cors.configurationSource(corsConfig));
        http.csrf(csrf -> csrf.disable());

        http.exceptionHandling(exception -> exception.authenticationEntryPoint(unauthorizedHandler));
        http.sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS));

        http.authorizeHttpRequests(auth ->
                auth
                        .requestMatchers(HttpMethod.OPTIONS, "/**").permitAll()
                        .requestMatchers("/internal/**").permitAll()

                        // ← SANS /api/ (le context-path le gère déjà)
                        .requestMatchers("/projects/**", "/documents/**", "/ai/**", "/error").permitAll()
                        .requestMatchers("/auth/**").permitAll()   // ← ajouter pour le login
                        .requestMatchers(getWhitelist().toArray(new String[0])).permitAll()
                        .anyRequest().authenticated()
        );
        http.authenticationProvider(authenticationProvider);
        http.addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }}