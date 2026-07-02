package com.binewvision.Motulbackend.entities.administration;


import com.binewvision.Motulbackend.entities.BaseEntity;
import com.binewvision.Motulbackend.enums.MailTemplateEnum;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.experimental.SuperBuilder;

@Entity
@Getter
@Setter
@Table(name = "mail_template")
@SuperBuilder
@AllArgsConstructor
@NoArgsConstructor
public class MailTemplateEntity extends BaseEntity {

    @Id
    @GeneratedValue(strategy=GenerationType.AUTO)
    private Long code;
    @Enumerated(EnumType.STRING)
    private MailTemplateEnum type;
    @Column(columnDefinition = "TEXT")
    private String content;
    @Column(columnDefinition = "TEXT")
    private String paragraph;
    private String objet;
}
