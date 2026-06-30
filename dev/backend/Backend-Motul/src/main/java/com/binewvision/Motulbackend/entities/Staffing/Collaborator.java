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

    @Column(nullable = false, length = 100)
    private String nom;

    @Column(nullable = false, length = 100)
    private String prenom;

    @Column(name = "date_demarrage", length = 50)
    private String dateDemarrage;

    @Column(name = "profil_professionnel", length = 200)
    private String profilProfessionnel;

    @Column(length = 50)
    private String anciennete;

    @Column(nullable = false)
    private Double salaire;
}
