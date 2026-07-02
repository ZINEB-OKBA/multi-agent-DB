package com.binewvision.Motulbackend.controllers.administration.authentication;

import com.binewvision.Motulbackend.dtos.administration.authentication.AttemptAuthenticationDto;
import com.binewvision.Motulbackend.services.administration.AttemptAuthenticationService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/attempt-authentications")
@RequiredArgsConstructor
public class AttemptAuthenticationController {

    private final AttemptAuthenticationService attemptAuthenticationService;

    @PostMapping(value = "/find")
    public ResponseEntity<Page<AttemptAuthenticationDto>> findAll(@RequestBody AttemptAuthenticationDto filter) {
        Page<AttemptAuthenticationDto> pages = attemptAuthenticationService.findAll(filter);
        return new ResponseEntity<>(pages, HttpStatus.OK);
    }
}
