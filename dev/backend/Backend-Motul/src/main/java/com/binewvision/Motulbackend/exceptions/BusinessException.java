package com.binewvision.Motulbackend.exceptions;


import lombok.Getter;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

import java.util.StringJoiner;

@Getter
@ResponseStatus(value = HttpStatus.INTERNAL_SERVER_ERROR)
public class BusinessException extends RuntimeException {
    private final HttpStatus statusCode;
    private final String message;
    public BusinessException(String message, HttpStatus status) {
        this.message = message;
        this.statusCode = status;
    }

    @Override
    public String toString() {
        return new StringJoiner(",", "(", ")")
                .add("Message : " + this.message)
                .add("Status Code : " + this.statusCode)
                .toString();
    }
}
