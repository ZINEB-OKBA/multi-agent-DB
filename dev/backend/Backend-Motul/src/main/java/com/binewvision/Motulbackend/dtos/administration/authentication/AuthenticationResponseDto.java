package com.binewvision.Motulbackend.dtos.administration.authentication;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

@Data
@NoArgsConstructor
@AllArgsConstructor
@SuperBuilder
public class AuthenticationResponseDto {
    private Long id;
    private String name;
    private String image;
    private String email;
    private String authority;
    private String accessToken;
    private String refreshToken;
    private boolean authenticate;
    private Long maxUpload;
}
