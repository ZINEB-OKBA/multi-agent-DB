package com.binewvision.Motulbackend.configuration;

import com.binewvision.Motulbackend.entities.administration.UserEntity;
import com.binewvision.Motulbackend.repositories.administration.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.authentication.dao.DaoAuthenticationProvider;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.client.RestTemplate;

import com.fasterxml.jackson.core.StreamReadConstraints;
import org.springframework.boot.autoconfigure.jackson.Jackson2ObjectMapperBuilderCustomizer;
import java.util.ArrayList;

@Configuration
@RequiredArgsConstructor
public class ApplicationConfig {

    private final UserRepository userRepository;

    @Bean
    public Jackson2ObjectMapperBuilderCustomizer jacksonCustomizer() {
        return builder -> builder.postConfigurer(objectMapper -> {
            objectMapper.getFactory().setStreamReadConstraints(
                StreamReadConstraints.builder()
                    .maxStringLength(200_000_000)
                    .build()
            );
        });
    }

    @Bean
    public UserDetailsService userDetailsService() {
        return username -> {
            // 1. On récupère d'abord votre entité utilisateur depuis la BDD
            UserEntity userEntity = userRepository.findByEmailAndDeletedFalse(username)
                    .orElseThrow(() -> new UsernameNotFoundException("User not found with email: " + username));

            // 2. On mappe l'entité vers l'objet User standard de Spring Security
            // (Ici avec une liste de rôles/autorisations vide, ou adaptez selon vos besoins)
            return User.builder()
                    .username(userEntity.getEmail())
                    .password(userEntity.getPassword()) // Doit déjà être hashé en BCrypt en BDD
                    .authorities(new ArrayList<>())     // Liste des privilèges (ou Rôles)
                    .build();
        };
    }

    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }

    @Bean
    public AuthenticationProvider authenticationProvider() {
        DaoAuthenticationProvider authProvider = new DaoAuthenticationProvider();
        authProvider.setUserDetailsService(userDetailsService());
        authProvider.setPasswordEncoder(passwordEncoder());
        return authProvider;
    }

    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration config) throws Exception {
        return config.getAuthenticationManager();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}