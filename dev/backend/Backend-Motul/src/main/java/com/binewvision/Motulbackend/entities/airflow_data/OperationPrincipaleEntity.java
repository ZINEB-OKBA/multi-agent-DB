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
@Table(name = "operations_principales", schema = "public")
public class OperationPrincipaleEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "date_appel_offres", nullable = false)
    private LocalDate dateAppelOffres;

    @Column(name = "date_de_valeur", nullable = false)
    private LocalDate dateDeValeur;

    @Column(name = "date_echeance")
    private LocalDate dateEcheance;

    @Column(name = "instrument", nullable = false)
    private String instrument;

    @Column(name = "montant_demande", nullable = false)
    private Double montantDemande;

    @Column(name = "montant_servi", nullable = false)
    private Double montantServi;

    @Column(name = "taux", nullable = false)
    private String taux;

}