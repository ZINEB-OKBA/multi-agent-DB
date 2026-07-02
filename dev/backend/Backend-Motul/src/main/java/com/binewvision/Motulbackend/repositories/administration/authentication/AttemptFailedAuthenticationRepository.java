package com.binewvision.Motulbackend.repositories.administration.authentication;

import com.binewvision.Motulbackend.entities.administration.authentication.AttemptFailedAuthenticationEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

import java.util.List;

public interface AttemptFailedAuthenticationRepository extends JpaRepository<AttemptFailedAuthenticationEntity, Long>, JpaSpecificationExecutor<AttemptFailedAuthenticationEntity> {
    List<AttemptFailedAuthenticationEntity> findAllByUsername(String username);

    void deleteAllByUsername(String username);
}
