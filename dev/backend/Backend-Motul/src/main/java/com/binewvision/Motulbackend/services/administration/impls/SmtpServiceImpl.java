package com.binewvision.Motulbackend.services.administration.impls;

import com.binewvision.Motulbackend.dtos.administration.SmtpDto;
import com.binewvision.Motulbackend.entities.administration.SmtpEntity;
import com.binewvision.Motulbackend.repositories.administration.SmtpRepository;
import com.binewvision.Motulbackend.security.config.AuthenticationFacade;
import com.binewvision.Motulbackend.services.administration.MailService;
import com.binewvision.Motulbackend.services.administration.SmtpService;
import com.binewvision.Motulbackend.utils.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class SmtpServiceImpl implements SmtpService {

    private final SmtpRepository smtpRepository;
    private final AuthenticationFacade authenticationFacade;
    private final MailService mailService;

    @Override
    public boolean testSmtpConfiguration() {
        Optional<SmtpEntity> optional;
        optional = smtpRepository.findById(0L);
        return optional.filter(this::testConnection).isPresent();
    }

    @Override
    public SmtpDto get() {
        Optional<SmtpEntity> optional;
        optional = smtpRepository.findById(0L);
        return optional.map(smtpEntity -> ObjectMapper.map(smtpEntity, SmtpDto.class)).orElse(null);
    }

    @Override
    public SmtpDto findById(Long id) {
        Optional<SmtpEntity> entity = smtpRepository.findById(id);
        if(entity.isPresent()){
            return ObjectMapper.map(entity, SmtpDto.class);
        }
        return null;
    }

    private boolean testConnection(SmtpEntity smtpEntity) {

        Map<String, String> model = new HashMap<>();

        // prepare content
        String content = "Test Connection";

        // prepare model
        model.put("content", content);
        model.put("receiver", smtpEntity.getUsername());
        model.put("subject", smtpEntity.getUsername());

        // send mail
        return mailService.send(model);
    }

    @Override
    public SmtpDto save(SmtpDto dto) {
        SmtpEntity entity = ObjectMapper.map(dto, SmtpEntity.class);

        if (entity.getId() == null){
            entity.setCreatedOn(LocalDateTime.now());
            entity.setCreatedBy(authenticationFacade.getCurrentUser());
        }else {
            entity.setUpdatedOn(LocalDateTime.now());
            entity.setUpdatedBy(authenticationFacade.getCurrentUser());
        }
        entity = smtpRepository.save(entity);
        return ObjectMapper.map(entity, SmtpDto.class);
    }


}