package com.binewvision.Motulbackend.services.administration;

import com.binewvision.Motulbackend.dtos.administration.ListeDto;
import org.springframework.data.domain.Page;

public interface ListService {
    Page<ListeDto> findAll(ListeDto filter);
    ListeDto findById(Long id);
    ListeDto save(ListeDto object);
    void delete(Long id);
}
