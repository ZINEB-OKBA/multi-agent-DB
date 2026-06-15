package com.binewvision.Motulbackend.services.airflow_data;

import com.binewvision.Motulbackend.dtos.airflow_data.IndiceMoniaDto;
import org.springframework.data.domain.Page;


public interface IndiceMoniaService {
    Page<IndiceMoniaDto> findAll(IndiceMoniaDto filter);
}
