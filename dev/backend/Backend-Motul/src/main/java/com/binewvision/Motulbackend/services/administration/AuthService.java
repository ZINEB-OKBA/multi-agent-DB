package com.binewvision.Motulbackend.services.administration;


import com.binewvision.Motulbackend.dtos.administration.UserDto;
import com.binewvision.Motulbackend.dtos.administration.authentication.AuthenticationResponseDto;

public interface AuthService {
    AuthenticationResponseDto authenticate(String email, String password);
    AuthenticationResponseDto refreshToken(String refreshToken);
    boolean setNewPassword(UserDto dto);
    boolean forgotPassword(String email);
    boolean updatePassword(UserDto dto);
}
