package com.binewvision.Motulbackend.services.airflow_data;

import com.binewvision.Motulbackend.dtos.airflow_data.MarcheMonetaireDto;
import org.springframework.data.domain.Page;


public interface MarcheMonetaireService {
    Page<MarcheMonetaireDto> findAll(MarcheMonetaireDto filter);
}
