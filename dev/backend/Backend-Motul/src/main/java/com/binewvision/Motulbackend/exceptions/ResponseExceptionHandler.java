package com.binewvision.Motulbackend.exceptions;

import com.binewvision.Motulbackend.dtos.HttpResponse;
import com.binewvision.Motulbackend.enums.ExceptionsEnum;
import io.jsonwebtoken.ExpiredJwtException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.dao.DataAccessException;
import org.springframework.dao.EmptyResultDataAccessException;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.DisabledException;
import org.springframework.security.authentication.LockedException;
import org.springframework.security.core.AuthenticationException;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;

import static java.time.LocalDateTime.now;
import static org.springframework.http.HttpStatus.*;

@Slf4j
@ControllerAdvice
public class ResponseExceptionHandler extends ResponseEntityExceptionHandler {

    // Gestion de l'exception lorsque les identifiants sont incorrects
    @ExceptionHandler(BadCredentialsException.class)
    public ResponseEntity<HttpResponse> badCredentialsException(BadCredentialsException exception) {
        log.error(exception.getMessage());
        return new ResponseEntity<>(
                HttpResponse.builder()
                        .timeStamp(now().toString())
                        .reason(ExceptionsEnum.BAD_CREDENTIALS.toString())
                        .status(UNAUTHORIZED)  // Renvoie un statut 401 Unauthorized
                        .statusCode(UNAUTHORIZED.value())
                        .build(), UNAUTHORIZED);
    }

    // Gestion de l'exception technique (erreur serveur interne)
    @ExceptionHandler(TechnicalException.class)
    public ResponseEntity<HttpResponse> technicalException(TechnicalException exception) {
        log.error(exception.getMessage());
        return new ResponseEntity<>(
                HttpResponse.builder()
                        .timeStamp(now().toString())
                        .reason(exception.getMessage())
                        .status(INTERNAL_SERVER_ERROR)  // Renvoie un statut 500 Internal Server Error
                        .statusCode(INTERNAL_SERVER_ERROR.value())
                        .build(), INTERNAL_SERVER_ERROR);
    }

    // Gestion de l'exception métier avec un code de statut spécifique
    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<HttpResponse> businessException(BusinessException exception) {
        log.error(exception.getMessage());
        return new ResponseEntity<>(
                HttpResponse.builder()
                        .timeStamp(now().toString())
                        .reason(exception.getMessage())
                        .status(exception.getStatusCode())
                        .statusCode(exception.getStatusCode().value())
                        .build(), exception.getStatusCode());
    }

    // Gestion de l'exception d'accès refusé lorsque l'utilisateur n'a pas les autorisations nécessaires
    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<HttpResponse> accessDeniedException(AccessDeniedException exception) {
        log.error("Access Denied: " + exception.getMessage());
        return new ResponseEntity<>(
                HttpResponse.builder()
                        .timeStamp(now().toString())
                        .reason(ExceptionsEnum.ACCESS_DENIED.toString())
                        .status(FORBIDDEN)  // Renvoie un statut 403 Forbidden
                        .statusCode(FORBIDDEN.value())
                        .build(), FORBIDDEN);
    }

    // Gestion de l'exception lorsque l'accès à une donnée est vide
    @ExceptionHandler(EmptyResultDataAccessException.class)
    public ResponseEntity<HttpResponse> emptyResultDataAccessException(EmptyResultDataAccessException exception) {
        log.error(exception.getMessage());
        return new ResponseEntity<>(
                HttpResponse.builder()
                        .timeStamp(now().toString())
                        .reason(ExceptionsEnum.DATA_NOT_FOUND.toString())
                        .status(BAD_REQUEST)  // Renvoie un statut 400 Bad Request
                        .statusCode(BAD_REQUEST.value())
                        .build(), BAD_REQUEST);
    }

    // Gestion de l'exception lorsque l'utilisateur est désactivé
    @ExceptionHandler(DisabledException.class)
    public ResponseEntity<HttpResponse> disabledException(DisabledException exception) {
        log.error(exception.getMessage());
        return new ResponseEntity<>(
                HttpResponse.builder()
                        .timeStamp(now().toString())
                        .reason(ExceptionsEnum.DISABLE_USER.toString())
                        .status(LOCKED)  // Renvoie un statut 423 Locked
                        .statusCode(LOCKED.value()).build(), LOCKED);
    }

    // Gestion de l'exception lorsque l'utilisateur est verrouillé
    @ExceptionHandler(LockedException.class)
    public ResponseEntity<HttpResponse> lockedException(LockedException exception) {
        log.error(exception.getMessage());
        return new ResponseEntity<>(
                HttpResponse.builder()
                        .timeStamp(now().toString())
                        .reason(ExceptionsEnum.LOCKED_USER.toString())
                        .status(LOCKED)  // Renvoie un statut 423 Locked
                        .statusCode(LOCKED.value()).build(), LOCKED);
    }

    // Gestion de l'exception d'accès aux données
    @ExceptionHandler(DataAccessException.class)
    public ResponseEntity<HttpResponse> dataAccessException(DataAccessException exception) {
        log.error(exception.getMessage());
        return new ResponseEntity<>(
                HttpResponse.builder()
                        .timeStamp(now().toString())
                        .reason(exception.getMessage())
                        .status(BAD_REQUEST)  // Renvoie un statut 400 Bad Request
                        .statusCode(BAD_REQUEST.value()).build(), BAD_REQUEST);
    }

    // Gestion de l'exception lorsque le token JWT est expiré
    @ExceptionHandler(ExpiredJwtException.class)
    public ResponseEntity<HttpResponse> authExpiredJwtException(ExpiredJwtException exception) {
        log.error(exception.getMessage());
        return new ResponseEntity<>(
                HttpResponse.builder()
                        .timeStamp(now().toString())
                        .reason(ExceptionsEnum.UNAUTHORIZED.toString())
                        .status(UNAUTHORIZED)  // Renvoie un statut 401 Unauthorized
                        .statusCode(UNAUTHORIZED.value()).build(), UNAUTHORIZED);
    }

    // Gestion de toutes les autres exceptions non spécifiées
    @ExceptionHandler(Exception.class)
    public ResponseEntity<HttpResponse> handleAllExceptions(Exception exception) {
        log.error("An unexpected error occurred: " + exception.getMessage());
        exception.printStackTrace();

        // Vérification si l'exception est liée à l'authentification
        if (exception instanceof AuthenticationException) {
            return new ResponseEntity<>(
                    HttpResponse.builder()
                            .timeStamp(now().toString())
                            .reason(ExceptionsEnum.UNAUTHORIZED.toString())
                            .status(UNAUTHORIZED)  // Renvoie un statut 401 Unauthorized
                            .statusCode(UNAUTHORIZED.value())
                            .build(), UNAUTHORIZED);
        } else if (exception instanceof AccessDeniedException) {
            return new ResponseEntity<>(
                    HttpResponse.builder()
                            .timeStamp(now().toString())
                            .reason(ExceptionsEnum.ACCESS_DENIED.toString())
                            .status(FORBIDDEN)  // Renvoie un statut 403 Forbidden
                            .statusCode(FORBIDDEN.value())
                            .build(), FORBIDDEN);
        }

        // Pour toutes les autres erreurs imprévues, renvoyer un statut 500 Internal Server Error
        return new ResponseEntity<>(
                HttpResponse.builder()
                        .timeStamp(now().toString())
                        .reason(ExceptionsEnum.TECHNICAL_ERROR.toString())
                        .status(INTERNAL_SERVER_ERROR)  // Renvoie un statut 500 Internal Server Error
                        .statusCode(INTERNAL_SERVER_ERROR.value())
                        .build(), INTERNAL_SERVER_ERROR);
    }

}

