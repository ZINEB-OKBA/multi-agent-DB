package com.binewvision.Motulbackend.dtos.administration;

import com.binewvision.Motulbackend.dtos.PageDto;
import com.binewvision.Motulbackend.enums.MailTemplateEnum;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

@Data
@NoArgsConstructor
@AllArgsConstructor
@SuperBuilder
public class MailTemplateDto {
    private Long code;
    private MailTemplateEnum type;
    private String content;
    private String paragraph;
    private String objet;
    private PageDto page;
    private String term;
}
