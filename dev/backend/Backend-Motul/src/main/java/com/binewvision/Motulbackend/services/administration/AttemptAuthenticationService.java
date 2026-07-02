package com.binewvision.Motulbackend.services.administration;


import com.binewvision.Motulbackend.dtos.administration.authentication.AttemptAuthenticationDto;
import com.binewvision.Motulbackend.entities.administration.UserEntity;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.data.domain.Page;
import org.springframework.security.authentication.event.AuthenticationFailureBadCredentialsEvent;
import org.springframework.security.authentication.event.AuthenticationSuccessEvent;

public interface AttemptAuthenticationService {

    Page<AttemptAuthenticationDto> findAll(AttemptAuthenticationDto filter);

    void save(HttpServletRequest request, AuthenticationSuccessEvent event);

    void failedSave(HttpServletRequest request, AuthenticationFailureBadCredentialsEvent event);

    boolean reachedMaxFailedAttempt(String username);

    void forgotPasswordSave(HttpServletRequest request, UserEntity user);

    boolean reachedMaxForgotPasswordAttempt(UserEntity user);

    void resetFailedAttempts(String username);

    void resetForogotPasswordAttempts(String username);
}
