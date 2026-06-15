package com.binewvision.Motulbackend.services.administration;


import com.binewvision.Motulbackend.dtos.administration.SmtpDto;

public interface SmtpService {
    boolean testSmtpConfiguration();
    SmtpDto get();
    SmtpDto findById(Long id);
    SmtpDto save(SmtpDto dto);
}
