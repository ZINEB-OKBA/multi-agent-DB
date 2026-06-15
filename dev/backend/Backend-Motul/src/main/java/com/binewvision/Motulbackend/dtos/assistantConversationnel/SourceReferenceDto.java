package com.binewvision.Motulbackend.dtos.assistantConversationnel;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class SourceReferenceDto {
    private String fileName;
    private String pages;
    private Integer extractCount;
}