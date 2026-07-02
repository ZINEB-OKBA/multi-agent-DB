package com.binewvision.Motulbackend.dtos.administration;

import com.binewvision.Motulbackend.dtos.PageDto;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

@Data
@NoArgsConstructor
@AllArgsConstructor
@SuperBuilder
public class ListeDto {

    private Long id;
    private String label;
    private String value;
    private ListeDto parent;
    private String nature;
    private PageDto page;
    private String term;
}

