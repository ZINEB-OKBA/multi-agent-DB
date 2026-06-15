package com.binewvision.Motulbackend.dtos.airflow_data;

import com.binewvision.Motulbackend.dtos.PageDto;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;

@NoArgsConstructor
@AllArgsConstructor
@Data
public class IndiceMoniaDto {
    private Long id;
    private String indiceMonia;
    private Double volumeJj;
    private LocalDate dateReference;
    private LocalDate datePublication;

    private LocalDate startDate;
    private LocalDate endDate;

    private PageDto page;
    private String term;
}
