package com.binewvision.Motulbackend.entities.airflow_data;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.math.BigDecimal;
import java.time.LocalDate;

@Getter
@Setter
@Entity
@NoArgsConstructor
@AllArgsConstructor
@Table(name = "asfim_data", schema = "public")
public class AsfimDataEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "classification")
    private String classification;

    @Column(name = "valeur_liquidative")
    private BigDecimal valeurLiquidative;

    @Column(name = "nature_juridique")
    private String natureJuridique;

    @Column(name = "souscripteurs")
    private String souscripteurs;

    @Column(name = "actif_net")
    private BigDecimal actifNet;

    @Column(name = "performance_5_ans")
    private BigDecimal performance5Ans;

    @Column(name = "periodicite_vl")
    private String periodiciteVl;

    @Column(name = "performance_1_semaine")
    private BigDecimal performance1Semaine;

    @Column(name = "performance_2_ans")
    private BigDecimal performance2Ans;

    @Column(name = "code_maroclear")
    private Long codeMaroclear;

    @Column(name = "categorie")
    private String categorie;

    @Column(name = "commission_souscription")
    private BigDecimal commissionSouscription;

    @Column(name = "performance_ytd")
    private BigDecimal performanceYtd;

    @Column(name = "affectation_resultats")
    private String affectationResultats;

    @Column(name = "frais_gestion")
    private BigDecimal fraisGestion;

    @Column(name = "date_depot")
    private LocalDate dateDepot;

    @Column(name = "commission_rachat")
    private BigDecimal commissionRachat;

    @Column(name = "performance_1_jour")
    private BigDecimal performance1Jour;

    @Column(name = "code_isin")
    private String codeIsin;

    @Column(name = "depositaire")
    private String depositaire;

    @Column(name = "performance_3_mois")
    private BigDecimal performance3Mois;

    @Column(name = "performance_1_an")
    private BigDecimal performance1An;

    @Column(name = "societe_gestion")
    private String societeGestion;

    @Column(name = "indice_benchmark")
    private String indiceBenchmark;

    @Column(name = "performance_1_mois")
    private BigDecimal performance1Mois;

    @Column(name = "performance_6_mois")
    private BigDecimal performance6Mois;

    @Column(name = "performance_3_ans")
    private BigDecimal performance3Ans;

    @Column(name = "fond")
    private String fond;

    @Column(name = "sensibilite")
    private String sensibilite;

    @Column(name = "reseau_placeur")
    private String reseauPlaceur;
}
