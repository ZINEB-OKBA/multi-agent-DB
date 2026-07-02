package com.binewvision.Motulbackend.services.assistantConversationnel;

import com.binewvision.Motulbackend.dtos.assistantConversationnel.ConversationDto;
import com.binewvision.Motulbackend.dtos.assistantConversationnel.MessageDto;
import org.springframework.data.domain.Page;

public interface ConversationService {
    Page<ConversationDto> findAll(ConversationDto filter);
    ConversationDto findById(Long id);
    void delete(Long id);
    MessageDto sendMessage(MessageDto object);
    ConversationDto renameConversation(ConversationDto conversation);
}
