package com.binewvision.Motulbackend.entities.Staffing;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "imputations")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class Imputation {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "nom_collaborateur", nullable = false, length = 100)
    private String nomCollaborateur;

    @Column(name = "prenom_collaborateur", nullable = false, length = 100)
    private String prenomCollaborateur;

    @Column(nullable = false, length = 100)
    private String projet;

    @Column(nullable = false, length = 10)
    private String mois;

    @Column(nullable = false, length = 10)
    private String annee;

    @Column(name = "nbr_jours", nullable = false)
    private Integer nbrJours;
}
