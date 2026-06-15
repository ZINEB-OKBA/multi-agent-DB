package com.binewvision.Motulbackend.dtos.airflow_data;

import com.binewvision.Motulbackend.dtos.PageDto;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;

@NoArgsConstructor
@AllArgsConstructor
@Data
public class CoursBilletDto {
    private Long id;
    private String devises;
    private Double achatClientele;
    private Double venteClientele;
    private LocalDate scrapingDate;

    private PageDto page;
    private String term;
}
