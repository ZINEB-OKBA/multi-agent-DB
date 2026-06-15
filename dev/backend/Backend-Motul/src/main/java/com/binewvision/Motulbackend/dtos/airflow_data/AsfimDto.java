package com.binewvision.Motulbackend.dtos.airflow_data;

import com.binewvision.Motulbackend.dtos.PageDto;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.time.LocalDateTime;

@NoArgsConstructor
@AllArgsConstructor
@Data
public class AsfimDto {
    private Long id;
    private String url;
    private String nomFichier;
    private String categorie;
    private LocalDate datePublication;
    private LocalDateTime dateExtraction;

    private PageDto page;
    private String term;
}
