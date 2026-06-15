package com.binewvision.Motulbackend.dtos.administration;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor @NoArgsConstructor
public class SmtpDto {
    private Long id;
    private String mailServer;
    private String sender;
    private String username;
    private String password;
    private Long port;
    private String encryptionMethod;
    private boolean auth;
}
