package com.binewvision.Motulbackend.services.airflow_data;

import com.binewvision.Motulbackend.dtos.airflow_data.CoursBilletDto;
import org.springframework.data.domain.Page;


public interface CoursBilletService {
    Page<CoursBilletDto> findAll(CoursBilletDto filter);
}
