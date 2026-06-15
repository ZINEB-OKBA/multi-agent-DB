package com.binewvision.Motulbackend.entities.administration.authentication;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

@Getter
@Setter
@Entity
@NoArgsConstructor
@AllArgsConstructor
@Table(name = "attempt_failed_authentication")
public class AttemptFailedAuthenticationEntity {

    @Id
    @GeneratedValue(strategy= GenerationType.AUTO)
    private Long id;
    private String browser;
    private String ip;
    private String username;
    private LocalDateTime createdOn;
}
