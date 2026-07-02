package com.binewvision.Motulbackend.repositories.administration;

import com.binewvision.Motulbackend.entities.administration.MailTemplateEntity;
import com.binewvision.Motulbackend.enums.MailTemplateEnum;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.stereotype.Repository;

@Repository
public interface MailTemplateRepository extends JpaRepository<MailTemplateEntity, Long>, JpaSpecificationExecutor<MailTemplateEntity> {

    MailTemplateEntity findByTypeAndDeletedFalse(MailTemplateEnum type);
}