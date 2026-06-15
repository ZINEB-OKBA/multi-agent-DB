package com.binewvision.Motulbackend.services.airflow_data;

import com.binewvision.Motulbackend.dtos.airflow_data.OperationPrincipaleDto;
import org.springframework.data.domain.Page;


public interface OperationPrincipaleService {
    Page<OperationPrincipaleDto> findAll(OperationPrincipaleDto filter);
}
