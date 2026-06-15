package com.binewvision.Motulbackend.entities.assistantConversationnel;

import com.binewvision.Motulbackend.entities.administration.UserEntity;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;
import java.util.List;

@Getter
@Setter
@Entity
@NoArgsConstructor
@AllArgsConstructor
@Table(name = "conversations")
public class ConversationEntity {
    @Id
    @GeneratedValue(strategy=GenerationType.AUTO)
    private Long id;
    private String name;
    @ManyToOne
    @JoinColumn(name = "createdBy")
    private UserEntity createdBy;
    private LocalDateTime createdOn;
    private LocalDateTime updatedOn;
    @Column(columnDefinition="boolean default false")
    private boolean deleted;
    @OneToMany()
    @JoinColumn(name = "messages")
    private List<MessageEntity> messages;
}
