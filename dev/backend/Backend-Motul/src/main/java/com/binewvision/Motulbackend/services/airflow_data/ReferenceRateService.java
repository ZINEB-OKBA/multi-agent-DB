package com.binewvision.Motulbackend.services.airflow_data;

import com.binewvision.Motulbackend.dtos.airflow_data.ReferenceRateDto;
import org.springframework.data.domain.Page;


public interface ReferenceRateService {
    Page<ReferenceRateDto> findAll(ReferenceRateDto filter);
}
