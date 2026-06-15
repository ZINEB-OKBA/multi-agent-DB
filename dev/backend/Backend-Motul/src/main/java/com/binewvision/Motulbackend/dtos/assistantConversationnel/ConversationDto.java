package com.binewvision.Motulbackend.dtos.assistantConversationnel;

import com.binewvision.Motulbackend.dtos.PageDto;
import com.binewvision.Motulbackend.dtos.administration.UserDto;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

import java.time.LocalDateTime;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
@SuperBuilder
public class ConversationDto {
    private Long id;
    private String name;
    @JsonIgnore
    private UserDto createdBy;
    private LocalDateTime createdOn;
    private LocalDateTime updatedOn;
    private boolean deleted;
    private List<MessageDto> messages;
    private PageDto page;
    private String term;
}
