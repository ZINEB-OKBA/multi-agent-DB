package com.binewvision.Motulbackend.services.airflow_data;

import com.binewvision.Motulbackend.dtos.airflow_data.AmmcDto;
import org.springframework.data.domain.Page;

public interface AmmcService {
    Page<AmmcDto> findAll(AmmcDto filter);
}
