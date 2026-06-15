package com.binewvision.Motulbackend.dtos.administration.authentication;

import com.binewvision.Motulbackend.dtos.PageDto;
import lombok.Data;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

@Data
@Getter
@Setter
public class AttemptAuthenticationDto {

    private Long id;
    private String browser;
    private String ip;
    private String username;
    private boolean success;
    private LocalDateTime createdOn;

    private String term;
    private PageDto page;
}
