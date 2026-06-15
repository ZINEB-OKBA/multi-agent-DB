package com.binewvision.Motulbackend.dtos.airflow_data;

import com.binewvision.Motulbackend.dtos.PageDto;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;

@NoArgsConstructor
@AllArgsConstructor
@Data
@Builder
public class AmmcDto {
    private Long id;
    private LocalDate date;
    private String url;
    private String titre;

    private PageDto page;
    private String term;
}
