package com.binewvision.Motulbackend.services.administration.impls;

import com.binewvision.Motulbackend.dtos.administration.MailTemplateDto;
import com.binewvision.Motulbackend.entities.administration.MailTemplateEntity;
import com.binewvision.Motulbackend.enums.MailTemplateEnum;
import com.binewvision.Motulbackend.repositories.administration.MailTemplateRepository;
import com.binewvision.Motulbackend.security.config.AuthenticationFacade;
import com.binewvision.Motulbackend.services.administration.MailTemplateService;
import com.binewvision.Motulbackend.utils.ObjectMapper;
import jakarta.persistence.criteria.Predicate;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class MailTemplateServiceImpl implements MailTemplateService {

    private final AuthenticationFacade authenticationFacade;
    private final MailTemplateRepository mailTemplateRepository;

    @Override
    public MailTemplateDto save(MailTemplateDto dto) {
        MailTemplateEntity entity = ObjectMapper.map(dto, MailTemplateEntity.class);
        if(entity.getCode() == null){
            entity.setCreatedOn(LocalDateTime.now());
            entity.setCreatedBy(authenticationFacade.getCurrentUser());
        }else {
            entity.setUpdatedOn(LocalDateTime.now());
            entity.setUpdatedBy(authenticationFacade.getCurrentUser());
        }
        entity = mailTemplateRepository.save(entity);
        return ObjectMapper.map(entity, MailTemplateDto.class);
    }

    @Override
    public Page<MailTemplateDto> findAll(MailTemplateDto filter) {
        int pageSize = filter.getPage().getSize();
        if (pageSize <= 0) {
            pageSize = Integer.MAX_VALUE;
        }
        Page<MailTemplateEntity> entities = mailTemplateRepository.findAll(getSpecification(filter), PageRequest.of(filter.getPage().getPage(), pageSize));
        return entities.map((object -> ObjectMapper.map(object, MailTemplateDto.class)));
    }

    private Specification<MailTemplateEntity> getSpecification(MailTemplateDto filter) {
        return (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();

            if (filter.getTerm() != null && !filter.getTerm().isEmpty()) {
                Predicate predicate_1 = cb.like(cb.lower(root.get("objet")), "%" + filter.getTerm().toLowerCase() + "%");
                predicates.add(cb.or(predicate_1));
            }

            predicates.add(cb.equal(root.get("deleted"), false));
            Predicate[] predicatesArray = new Predicate[predicates.size()];
            return cb.and(predicates.toArray(predicatesArray));
        };
    }

    @Override
    public MailTemplateDto findById(Long id) {
        Optional<MailTemplateEntity> entity = mailTemplateRepository.findById(id);
        if(entity.isPresent()){
            return ObjectMapper.map(entity, MailTemplateDto.class);
        }
        return null;
    }

    @Override
    public MailTemplateDto findByType(MailTemplateEnum type) {
        MailTemplateEntity entity = mailTemplateRepository.findByTypeAndDeletedFalse(type);
        if (entity != null) {
            return ObjectMapper.map(entity, MailTemplateDto.class);
        }
        return null;
    }

    @Override
    public void delete(Long id) {
        Optional<MailTemplateEntity> optional = mailTemplateRepository.findById(id);
        if(optional.isPresent()){
            MailTemplateEntity entity = optional.get();
            entity.setDeleted(true);
            mailTemplateRepository.save(entity);
        }
    }
}
