package com.binewvision.Motulbackend.controllers.administration.authentication;

import com.binewvision.Motulbackend.dtos.administration.UserDto;
import com.binewvision.Motulbackend.dtos.administration.authentication.AuthenticationResponseDto;
import com.binewvision.Motulbackend.services.administration.AuthService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthenticationController {
    private final AuthService authService;

    @PostMapping("/authenticate")
    public ResponseEntity<AuthenticationResponseDto> authenticate(@RequestBody UserDto dto) {
        return ResponseEntity.ok(authService.authenticate(dto.getEmail(), dto.getPassword()));
    }

    @PostMapping("/refresh-token")
    public ResponseEntity<?> refreshToken(@RequestBody String refreshToken) {
        AuthenticationResponseDto authenticationResponseDto = authService.refreshToken(refreshToken);
        if(authenticationResponseDto == null) {
            return new ResponseEntity<>(HttpStatus.UNAUTHORIZED);
        }
        return ResponseEntity.ok(authenticationResponseDto);
    }
    @PostMapping("/new-password")
    public ResponseEntity<Boolean> setNewPassword(@RequestBody UserDto dto) {
        return ResponseEntity.ok(authService.setNewPassword(dto));
    }

    @PostMapping("/forgot-password")
    public ResponseEntity<Boolean> forgotPassword(@RequestBody String email) {
        return ResponseEntity.ok(authService.forgotPassword(email));
    }

    @PostMapping("/update-password")
    public ResponseEntity<Boolean> updatePassword(@RequestBody UserDto dto) {
        return ResponseEntity.ok(authService.updatePassword(dto));
    }

}
