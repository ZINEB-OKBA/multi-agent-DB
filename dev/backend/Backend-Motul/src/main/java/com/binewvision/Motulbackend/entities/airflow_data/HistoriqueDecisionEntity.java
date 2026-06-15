package com.binewvision.Motulbackend.entities.airflow_data;


import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDate;

@Getter
@Setter
@Entity
@NoArgsConstructor
@AllArgsConstructor
@Table(name = "historique_decision", schema = "public")
public class HistoriqueDecisionEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "date")
    private LocalDate date;

    @Column(name = "taux_directeur")
    private String tauxDirecteur;

    @Column(name = "ratio_de_réserve_obligatoire", columnDefinition = "text")
    private String ratioDeReserveObligatoire;

    @Column(name = "remuneration_de_la_reserve", nullable = false, columnDefinition = "text")
    private String remunerationDeLaReserve;
}