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

    @Column(nullable = false, length = 200)
    private String collaborateur;

    @Column(name = "collaborateur_id")
    private Long collaborateurId;

    @Column(nullable = false, length = 100)
    private String projet;

    @Column(name = "projet_id")
    private Long projetId;

    @Column(nullable = false, length = 10)
    private String mois;

    @Column(nullable = false, length = 10)
    private String annee;

    @Column(name = "nbr_jours", nullable = false)
    private Integer nbrJours;
}
