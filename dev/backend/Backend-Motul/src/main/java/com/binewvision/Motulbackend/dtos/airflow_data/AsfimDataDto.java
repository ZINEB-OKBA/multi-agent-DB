package com.binewvision.Motulbackend.dtos.airflow_data;

import com.binewvision.Motulbackend.dtos.PageDto;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDate;

@NoArgsConstructor
@AllArgsConstructor
@Data
@Builder
public class AsfimDataDto {

    private Long id;

    private String classification;
    private BigDecimal valeurLiquidative;
    private String natureJuridique;
    private String souscripteurs;
    private BigDecimal actifNet;
    private BigDecimal performance5Ans;
    private String periodiciteVl;
    private BigDecimal performance1Semaine;
    private BigDecimal performance2Ans;
    private Long codeMaroclear;
    private String categorie;
    private BigDecimal commissionSouscription;
    private BigDecimal performanceYtd;
    private String affectationResultats;
    private BigDecimal fraisGestion;
    private LocalDate dateDepot;
    private BigDecimal commissionRachat;
    private BigDecimal performance1Jour;
    private String codeIsin;
    private String depositaire;
    private BigDecimal performance3Mois;
    private BigDecimal performance1An;
    private String societeGestion;
    private String indiceBenchmark;
    private BigDecimal performance1Mois;
    private BigDecimal performance6Mois;
    private BigDecimal performance3Ans;
    private String fond;
    private String sensibilite;
    private String reseauPlaceur;

    private LocalDate dateDepotFrom;
    private LocalDate dateDepotTo;

    private PageDto page;
    private String term;
}
