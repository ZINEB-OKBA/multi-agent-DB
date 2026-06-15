package com.binewvision.Motulbackend.services.airflow_data;

import com.binewvision.Motulbackend.dtos.airflow_data.BandeFluctuationsDto;
import org.springframework.data.domain.Page;


public interface BandeFluctuationsService {
    Page<BandeFluctuationsDto> findAll(BandeFluctuationsDto filter);
}
