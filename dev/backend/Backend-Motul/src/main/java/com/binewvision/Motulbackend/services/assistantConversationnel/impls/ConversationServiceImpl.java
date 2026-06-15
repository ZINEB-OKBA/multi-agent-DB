package com.binewvision.Motulbackend.services.assistantConversationnel.impls;

import com.binewvision.Motulbackend.dtos.PageDto;
import com.binewvision.Motulbackend.dtos.administration.UserDto;
import com.binewvision.Motulbackend.dtos.assistantConversationnel.ConversationDto;
import com.binewvision.Motulbackend.dtos.assistantConversationnel.MessageDto;
import com.binewvision.Motulbackend.dtos.assistantConversationnel.SourceReferenceDto;
import com.binewvision.Motulbackend.entities.administration.UserEntity;
import com.binewvision.Motulbackend.entities.assistantConversationnel.ConversationEntity;
import com.binewvision.Motulbackend.entities.assistantConversationnel.MessageEntity;
import com.binewvision.Motulbackend.enums.SenderEnum;
import com.binewvision.Motulbackend.repositories.administration.UserRepository;
import com.binewvision.Motulbackend.repositories.assistantConversationnel.ConversationRepository;
import com.binewvision.Motulbackend.repositories.assistantConversationnel.MessageRepository;
import com.binewvision.Motulbackend.security.config.AuthenticationFacade;
import com.binewvision.Motulbackend.services.assistantConversationnel.AiService;
import com.binewvision.Motulbackend.services.assistantConversationnel.ConversationService;
import com.binewvision.Motulbackend.configuration.ApplicationProperties;
import com.binewvision.Motulbackend.utils.ObjectMapper;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import jakarta.persistence.criteria.Predicate;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.http.*;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ConversationServiceImpl implements ConversationService {

    private static final Logger logger = LoggerFactory.getLogger(ConversationServiceImpl.class);

    private final ConversationRepository conversationRepository;
    private final AuthenticationFacade authenticationFacade;
    private final UserRepository userRepository;
    private final MessageRepository messageRepository;
    private final AiService aiService;
    private final RestTemplate restTemplate;
    private final com.fasterxml.jackson.databind.ObjectMapper jacksonObjectMapper;
    private final ApplicationProperties applicationProperties;

    @Override
    public Page<ConversationDto> findAll(ConversationDto filter) {
        Page<ConversationEntity> entities = conversationRepository.findAll(
                getSpecification(filter),
                getPageRequest(filter.getPage())
        );
        return entities.map(object -> ObjectMapper.map(object, ConversationDto.class));
    }

    @Override
    public ConversationDto findById(Long id) {
        ConversationEntity conversationEntity = conversationRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("CONVERSATION_NOT_FOUND"));
        ConversationDto conversationDto = ObjectMapper.map(conversationEntity, ConversationDto.class);

        List<MessageEntity> messages = messageRepository.findByConversationIdOrderByIdAsc(id);
        List<MessageDto> messageDtos = messages.stream()
                .map(message -> {
                    MessageDto dto = ObjectMapper.map(message, MessageDto.class);

                    // ── DÉSÉRIALISATION DES SOURCES POUR L'HISTORIQUE ──
                    if (message.getSourcesJson() != null && !message.getSourcesJson().isEmpty()) {
                        try {
                            List<SourceReferenceDto> sources = jacksonObjectMapper.readValue(
                                    message.getSourcesJson(),
                                    new TypeReference<List<SourceReferenceDto>>() {}
                            );
                            dto.setSources(sources);
                        } catch (Exception e) {
                            logger.error("Erreur de lecture des sources JSON pour le message {}", message.getId(), e);
                            dto.setSources(new ArrayList<>());
                        }
                    } else {
                        dto.setSources(new ArrayList<>());
                    }
                    return dto;
                })
                .collect(Collectors.toList());

        conversationDto.setMessages(messageDtos);
        return conversationDto;
    }

    @Override
    public void delete(Long id) {
        Optional<ConversationEntity> optional = conversationRepository.findById(id);
        if (optional.isPresent()) {
            ConversationEntity entity = optional.get();
            entity.setDeleted(true);
            conversationRepository.save(entity);
        }
    }

    @Override
    public MessageDto sendMessage(MessageDto object) {

        // ── A. Récupérer ou créer la conversation ─────────────────────────────
        ConversationEntity conversation;
        if (object.getConversation() != null && object.getConversation().getId() != null) {
            conversation = conversationRepository.findById(object.getConversation().getId())
                    .orElseThrow(() -> new RuntimeException("CONVERSATION_NOT_FOUND"));
        } else {
            // Nouvelle conversation : créer et sauvegarder
            UserEntity currentUser = userRepository
                    .findByEmailAndDeletedFalse(authenticationFacade.getCurrentUser())
                    .orElseThrow(() -> new RuntimeException("USER_NOT_FOUND"));

            conversation = new ConversationEntity();
            conversation.setName(
                    object.getContent().length() > 40
                            ? object.getContent().substring(0, 40) + "..."
                            : object.getContent()
            );
            conversation.setCreatedBy(currentUser);
            conversation.setCreatedOn(LocalDateTime.now());
            conversation.setDeleted(false);
            conversation = conversationRepository.save(conversation);
        }

        // ── B. Sauvegarder le message utilisateur ─────────────────────────────
        MessageEntity userMessage = new MessageEntity();
        userMessage.setConversation(conversation);
        userMessage.setContent(object.getContent());
        userMessage.setSendBy(SenderEnum.USER);
        userMessage.setSendOn(LocalDateTime.now());
        messageRepository.save(userMessage);

        // ── C. Appel Python FastAPI ───────────────────────────────────────────
        String fastApiUrl = applicationProperties.getExternalAiConfig().getUrl();
        Map<String, Object> pythonPayload = Map.of(
                "question", object.getContent(),
                "project",  object.getProject() != null ? object.getProject() : ""
        );

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> request = new HttpEntity<>(pythonPayload, headers);

        // ── D. Parser la réponse Python avec JsonNode (plus sûr) ─────────────
        String   agentAnswer = "Erreur : impossible de contacter l'IA.";
        List<SourceReferenceDto> sources = new ArrayList<>();

        try {
            ResponseEntity<JsonNode> response = restTemplate.exchange(
                    fastApiUrl, HttpMethod.POST, request, JsonNode.class
            );

            JsonNode body = response.getBody();
            if (body != null) {
                // Extraire la réponse texte
                agentAnswer = body.path("answer").asText("Aucune réponse.");

                // Extraire les sources [ {fileName, pages, extractCount} ]
                JsonNode sourcesNode = body.path("sources");
                if (sourcesNode.isArray()) {
                    for (JsonNode src : sourcesNode) {
                        SourceReferenceDto dto = new SourceReferenceDto();
                        dto.setFileName(src.path("fileName").asText(""));
                        dto.setPages(src.path("pages").isNull() ? null : src.path("pages").asText());
                        dto.setExtractCount(src.path("extractCount").asInt(0));
                        sources.add(dto);
                    }
                }
            }
        } catch (Exception e) {
            logger.error("Erreur appel Python FastAPI : {}", e.getMessage(), e);
        }

        // ── E. Sauvegarder le message AGENT en BDD ────────────────────────────
        String sourcesJson = "[]";
        try {
            sourcesJson = jacksonObjectMapper.writeValueAsString(sources);
        } catch (Exception e) {
            logger.error("Erreur de sérialisation des sources", e);
        }

        MessageEntity agentEntity = new MessageEntity();
        agentEntity.setConversation(conversation);
        agentEntity.setContent(agentAnswer);
        agentEntity.setSendBy(SenderEnum.AGENT);
        agentEntity.setSendOn(LocalDateTime.now());
        agentEntity.setSourcesJson(sourcesJson);
        messageRepository.save(agentEntity);

        // ── F. Construire le DTO de retour vers Angular ───────────────────────
        MessageDto responseDto = new MessageDto();
        responseDto.setId(agentEntity.getId());
        responseDto.setContent(agentAnswer);
        responseDto.setSendBy(SenderEnum.AGENT);
        responseDto.setSendOn(agentEntity.getSendOn());
        responseDto.setProject(object.getProject());
        responseDto.setSources(sources);
        responseDto.setConversation(
                ObjectMapper.map(conversation, ConversationDto.class)
        );

        return responseDto;
    }

    @Override
    public ConversationDto renameConversation(ConversationDto conversation) {
        UserEntity currentUser = userRepository
                .findByEmailAndDeletedFalse(authenticationFacade.getCurrentUser())
                .orElseThrow(() -> new RuntimeException("USER_NOT_FOUND"));
        conversation.setName(conversation.getName());
        conversation.setUpdatedOn(LocalDateTime.now());
        conversation.setCreatedBy(ObjectMapper.map(currentUser, UserDto.class));
        conversationRepository.save(ObjectMapper.map(conversation, ConversationEntity.class));
        return conversation;
    }

    private Specification<ConversationEntity> getSpecification(ConversationDto filter) {
        return (root, query, criteriaBuilder) -> {
            List<Predicate> predicates = new ArrayList<>();

            UserEntity currentUser = userRepository.findByEmailAndDeletedFalse(authenticationFacade.getCurrentUser())
                    .orElseThrow(() -> new UsernameNotFoundException("USER_NOT_FOUND"));

            predicates.add(criteriaBuilder.equal(root.get("createdBy").get("id"), currentUser.getId()));

            if (filter.getTerm() != null && !filter.getTerm().isEmpty()) {
                Predicate predicate_1 = criteriaBuilder.like(
                        criteriaBuilder.lower(root.get("name")),
                        "%" + filter.getTerm().toLowerCase() + "%"
                );
                predicates.add(criteriaBuilder.or(predicate_1));
            }

            if (query != null) {
                query.orderBy(criteriaBuilder.desc(root.get("id")));
            }
            predicates.add(criteriaBuilder.equal(root.<Boolean>get("deleted"), false));

            return criteriaBuilder.and(predicates.toArray(new Predicate[0]));
        };
    }

    private PageRequest getPageRequest(PageDto pageDto) {
        int pageSize = pageDto.getSize();
        if (pageSize <= 0) {
            pageSize = Integer.MAX_VALUE;
        }
        int pageNumber = pageDto.getPage();
        if (pageDto.isSortable()) {
            String directionStr = pageDto.getDirection();
            String column = pageDto.getColumn();

            Sort.Direction direction = Sort.Direction.ASC;
            if ("DESC".equalsIgnoreCase(directionStr)) {
                direction = Sort.Direction.DESC;
            }

            Sort sort = Sort.by(direction, column);
            return PageRequest.of(pageNumber, pageSize, sort);
        }
        return PageRequest.of(pageNumber, pageSize);
    }
}