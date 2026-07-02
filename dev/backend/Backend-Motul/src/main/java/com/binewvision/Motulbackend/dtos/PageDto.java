package com.binewvision.Motulbackend.dtos;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@NoArgsConstructor
@AllArgsConstructor
@Data
public class PageDto {

    private List<?> content;
    private int page;
    private int size;
    private int totalElements;
    private boolean sortable;
    private String direction;
    private String column;

}
