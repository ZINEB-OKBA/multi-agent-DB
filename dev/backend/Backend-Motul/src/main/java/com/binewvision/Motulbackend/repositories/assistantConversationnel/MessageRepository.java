package com.binewvision.Motulbackend.repositories.assistantConversationnel;

import com.binewvision.Motulbackend.entities.assistantConversationnel.MessageEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface MessageRepository extends JpaRepository<MessageEntity,Long>, JpaSpecificationExecutor<MessageEntity> {
    List<MessageEntity> findByConversationIdOrderByIdAsc(Long conversationId);
}
