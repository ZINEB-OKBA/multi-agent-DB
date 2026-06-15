package com.binewvision.Motulbackend.repositories.administration.authentication;

import com.binewvision.Motulbackend.entities.administration.authentication.AttemptAuthenticationEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

public interface AttemptAuthenticationRepository extends JpaRepository<AttemptAuthenticationEntity, Long>, JpaSpecificationExecutor<AttemptAuthenticationEntity> {
}
