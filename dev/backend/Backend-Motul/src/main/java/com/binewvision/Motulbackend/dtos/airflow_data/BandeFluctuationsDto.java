package com.binewvision.Motulbackend.dtos.airflow_data;

import com.binewvision.Motulbackend.dtos.PageDto;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.time.LocalTime;

@NoArgsConstructor
@AllArgsConstructor
@Data
public class BandeFluctuationsDto {
    private Long id;
    private String devises;
    private LocalTime heure;
    private Double coursMinimum;
    private Double coursMaximum;
    private LocalDate scrapingDate;

    private LocalDate startDate;
    private LocalDate endDate;


    private PageDto page;
    private String term;
}
