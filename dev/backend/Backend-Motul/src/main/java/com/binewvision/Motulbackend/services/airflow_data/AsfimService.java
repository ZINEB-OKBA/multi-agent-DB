package com.binewvision.Motulbackend.services.airflow_data;

import com.binewvision.Motulbackend.dtos.airflow_data.AsfimDto;
import org.springframework.data.domain.Page;


public interface AsfimService {
    Page<AsfimDto> findAll(AsfimDto filter);
}
