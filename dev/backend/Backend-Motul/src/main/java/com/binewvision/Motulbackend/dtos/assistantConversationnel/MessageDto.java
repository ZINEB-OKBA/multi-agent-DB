package com.binewvision.Motulbackend.dtos.assistantConversationnel;

import com.binewvision.Motulbackend.dtos.PageDto;
import com.binewvision.Motulbackend.enums.SenderEnum;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Data
@NoArgsConstructor
@AllArgsConstructor
@SuperBuilder
public class MessageDto {
    private Long id;
    private ConversationDto conversation;
    private String content;
    private String project;
    private LocalDateTime sendOn;
    private SenderEnum sendBy;
    private PageDto page;
    private String term;

    // ── TRANSMISSION DES SOURCES VERS LE FRONTEND ANGULAR ──
    // Contient la liste d'objets structurés mappés depuis ou vers sourcesJson
    private List<SourceReferenceDto> sources;

    // ── TRANSMISSION DES GRAPHES VERS LE FRONTEND ANGULAR ──
    private List<Map<String, Object>> charts;
}