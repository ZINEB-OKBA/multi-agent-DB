package com.binewvision.Motulbackend.entities.administration;

import com.binewvision.Motulbackend.entities.BaseEntity;
import com.binewvision.Motulbackend.enums.SmtpEncryptionMethodEnum;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@Table(name = "smtp")
public class SmtpEntity extends BaseEntity {
    @Id
    @SequenceGenerator(initialValue = 1, name = "smtp_seq", sequenceName = "smtp_sequence", allocationSize = 1)
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "smtp_seq")
    private Long id;
    private String mailServer;
    private String sender;
    private String username;
    private String password;
    private Long port;
    @Enumerated(EnumType.STRING)
    private SmtpEncryptionMethodEnum encryptionMethod;
    private boolean auth;
}