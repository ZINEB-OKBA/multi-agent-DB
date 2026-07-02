package com.binewvision.Motulbackend.repositories.administration;

import com.binewvision.Motulbackend.entities.administration.SmtpEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.stereotype.Repository;

@Repository
public interface SmtpRepository extends JpaRepository<SmtpEntity, Long>, JpaSpecificationExecutor<SmtpEntity> {

}