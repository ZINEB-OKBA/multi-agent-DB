package com.binewvision.Motulbackend.dtos.airflow_data;

import com.binewvision.Motulbackend.dtos.PageDto;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;

@NoArgsConstructor
@AllArgsConstructor
@Data
public class OperationPrincipaleDto {
    private Long id;
    private LocalDate dateAppelOffres;
    private LocalDate dateDeValeur;
    private LocalDate dateEcheance;
    private String instrument;
    private Double montantDemande;
    private Double montantServi;
    private String taux;

    private LocalDate startDate;
    private LocalDate endDate;

    private PageDto page;
    private String term;
}
