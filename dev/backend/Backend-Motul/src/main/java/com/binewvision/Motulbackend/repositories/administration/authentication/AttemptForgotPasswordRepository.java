package com.binewvision.Motulbackend.repositories.administration.authentication;

import com.binewvision.Motulbackend.entities.administration.authentication.AttemptForgotPasswordEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

import java.util.List;

public interface AttemptForgotPasswordRepository extends JpaRepository<AttemptForgotPasswordEntity, Long>, JpaSpecificationExecutor<AttemptForgotPasswordEntity> {
    List<AttemptForgotPasswordEntity> findAllByUsername(String username);
    void deleteAllByUsername(String username);
}
