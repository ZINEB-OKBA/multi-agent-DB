package com.binewvision.Motulbackend.repositories.assistantConversationnel;

import com.binewvision.Motulbackend.entities.assistantConversationnel.ConversationEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.stereotype.Repository;

@Repository
public interface ConversationRepository extends JpaRepository<ConversationEntity,Long>, JpaSpecificationExecutor<ConversationEntity> {

}
