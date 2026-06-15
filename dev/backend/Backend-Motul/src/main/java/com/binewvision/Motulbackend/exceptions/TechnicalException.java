package com.binewvision.Motulbackend.exceptions;


import lombok.Getter;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

import java.util.StringJoiner;

@Getter
@ResponseStatus(value = HttpStatus.INTERNAL_SERVER_ERROR)
public class TechnicalException extends RuntimeException {
    private final String message;
    private final Throwable throwable;

    public TechnicalException(String message, Throwable e) {
        this.message = message;
        this.throwable = e;
        e.printStackTrace();
    }


    @Override
    public String toString() {
        return new StringJoiner(",", "(", ")")
                .add("Message : " + this.message)
                .add("Class : " + this.throwable)
                .toString();
    }
}
