package com.binewvision.Motulbackend.entities.Staffing;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "collaborateurs")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class Collaborator {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 200)
    private String collaborateur;

    @Column(name = "date_demarrage", nullable = false, length = 50)
    private String dateDemarrage;

    @Column(name = "profil_professionnel", nullable = false, length = 200)
    private String profilProfessionnel;

    @Column(nullable = false, length = 50)
    private String anciennete;

    @Column(nullable = false)
    private Double salaire;
}
