package com.binewvision.Motulbackend.services.airflow_data;

import com.binewvision.Motulbackend.dtos.airflow_data.HistoriqueDecisionDto;
import org.springframework.data.domain.Page;


public interface HistoriqueDecisionService {
    Page<HistoriqueDecisionDto> findAll(HistoriqueDecisionDto filter);
}
