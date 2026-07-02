package com.binewvision.Motulbackend.services.administration;

import com.binewvision.Motulbackend.dtos.administration.MailTemplateDto;
import com.binewvision.Motulbackend.enums.MailTemplateEnum;
import org.springframework.data.domain.Page;

public interface MailTemplateService {
    MailTemplateDto save(MailTemplateDto dto);
    Page<MailTemplateDto> findAll(MailTemplateDto filter);
    MailTemplateDto findById(Long id);
    MailTemplateDto findByType(MailTemplateEnum type);
    void delete(Long id);
}
