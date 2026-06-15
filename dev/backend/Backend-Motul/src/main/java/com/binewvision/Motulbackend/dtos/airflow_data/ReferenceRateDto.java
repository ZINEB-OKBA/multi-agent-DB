package com.binewvision.Motulbackend.dtos.airflow_data;

import com.binewvision.Motulbackend.dtos.PageDto;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;

@NoArgsConstructor
@AllArgsConstructor
@Data
public class ReferenceRateDto {
    private Long id;
    private String devise;
    private Double moyen;
    private LocalDate date;

    private LocalDate startDate;
    private LocalDate endDate;

    private PageDto page;
    private String term;
}
