package com.binewvision.Motulbackend.dtos.airflow_data;

import com.binewvision.Motulbackend.dtos.PageDto;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;

@NoArgsConstructor
@AllArgsConstructor
@Data
public class MarcheMonetaireDto {
    private Long id;
    private LocalDate date;
    private Double tauxMoyenPondere;
    private Double volumeJj;
    private Double encours;

    private LocalDate startDate;
    private LocalDate endDate;

    private PageDto page;
    private String term;
}
