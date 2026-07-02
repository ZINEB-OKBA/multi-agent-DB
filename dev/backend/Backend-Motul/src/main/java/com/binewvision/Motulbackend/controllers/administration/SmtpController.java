package com.binewvision.Motulbackend.controllers.administration;

import com.binewvision.Motulbackend.dtos.administration.SmtpDto;
import com.binewvision.Motulbackend.services.administration.SmtpService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/smtp")
@RequiredArgsConstructor
public class SmtpController {
    private final SmtpService smtpService;
    @GetMapping("/test")
    public ResponseEntity<Boolean> testSmtp() {
        boolean result = smtpService.testSmtpConfiguration();
        return new ResponseEntity<>(result, HttpStatus.OK);
    }

    @GetMapping(value = "/get")
    public ResponseEntity<SmtpDto> get(){
        SmtpDto dto = smtpService.get();
        return new ResponseEntity<>(dto, HttpStatus.OK);
    }

    @PostMapping(value = "/save")
    public ResponseEntity<SmtpDto> save(@RequestBody SmtpDto dto){
        dto = smtpService.save(dto);
        return new ResponseEntity<>(dto, HttpStatus.OK);
    }
}