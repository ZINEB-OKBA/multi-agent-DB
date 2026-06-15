package com.binewvision.Motulbackend.services.airflow_data;

import com.binewvision.Motulbackend.dtos.airflow_data.AsfimDataDto;
import org.springframework.data.domain.Page;


public interface AsfimDataService {
    Page<AsfimDataDto> findAll(AsfimDataDto filter);
}
