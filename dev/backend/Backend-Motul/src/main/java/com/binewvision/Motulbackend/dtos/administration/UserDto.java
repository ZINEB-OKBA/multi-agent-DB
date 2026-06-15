package com.binewvision.Motulbackend.dtos.administration;

import com.binewvision.Motulbackend.dtos.PageDto;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;
import org.apache.tomcat.util.codec.binary.Base64;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.time.LocalDateTime;
import java.util.Collection;
import java.util.Collections;
import java.util.stream.Collectors;

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
public class UserDto implements UserDetails {

    private Long id;
    private String firstName;
    private String lastName;
    private String email;
    @JsonProperty(access = JsonProperty.Access.WRITE_ONLY)
    private String password;
    private String phone;
    private String image;
    private String address;
    private String term;
    private boolean enabled;
    private boolean locked;
    private LocalDateTime createdAt;
    private ProfileDto profile;
    private ListeDto service;
    private PageDto page;
    private String otp;
    private String currentPassword;
    private String newPassword;
    private String createdBy;
    private String updatedBy;
    private LocalDateTime createdOn;
    private LocalDateTime updatedOn;
    private boolean deleted;
    private String secret;

    /**
     * Version sécurisée pour éviter le NullPointerException (Erreur 500) au Login
     * s'exécute parfaitement pour les profils Admin, User, ou les profils sans rôles.
     */
    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        // 🛡️ Si le profil est nul ou si la liste des rôles n'est pas initialisée
        if (this.profile == null || this.profile.getRoles() == null) {
            // Renvoie une liste vide propre au lieu de faire s'effondrer Spring Security
            return Collections.emptyList();
        }

        return this.profile.getRoles().stream()
                .filter(role -> role != null && role.getIdentifiant() != null) // Évite les données partielles vides
                .map(role -> new SimpleGrantedAuthority(role.getIdentifiant()))
                .collect(Collectors.toList());
    }

    @Override
    public String getPassword() {
        return this.password;
    }

    @Override
    public String getUsername() {
        return this.email;
    }

    @Override
    public boolean isAccountNonExpired() {
        return true;
    }

    @Override
    public boolean isAccountNonLocked() {
        return !this.locked;
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return true;
    }

    @Override
    public boolean isEnabled() {
        return this.enabled;
    }

    public void setImage(Object image) {
        if (image instanceof String) {
            this.image = (String) image;
        } else if (image instanceof byte[]) {
            this.image = Base64.encodeBase64String((byte[]) image);
        } else {
            this.image = null;
        }
    }
}