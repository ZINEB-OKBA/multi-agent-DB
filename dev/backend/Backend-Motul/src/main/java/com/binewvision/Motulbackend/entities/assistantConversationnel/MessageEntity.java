package com.binewvision.Motulbackend.entities.assistantConversationnel;

import com.binewvision.Motulbackend.enums.SenderEnum;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

@Getter
@Setter
@Entity
@NoArgsConstructor
@AllArgsConstructor
@Table(name = "messages")
public class MessageEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "conversation")
    private ConversationEntity conversation;

    @Column(columnDefinition = "text")
    private String content;

    private LocalDateTime sendOn;

    @Enumerated(EnumType.STRING)
    private SenderEnum sendBy;

    // ── CONFIGURATION DES SOURCES ──
    // Stocké sous forme de chaîne JSON TEXT : "[{\"fileName\":\"...\",\"pages\":\"...\",\"extractCount\":1}]"
    @Column(columnDefinition = "TEXT")
    private String sourcesJson;
}