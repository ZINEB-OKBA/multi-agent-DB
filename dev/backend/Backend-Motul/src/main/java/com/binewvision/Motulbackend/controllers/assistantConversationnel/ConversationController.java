package com.binewvision.Motulbackend.controllers.assistantConversationnel;

import com.binewvision.Motulbackend.dtos.assistantConversationnel.ConversationDto;
import com.binewvision.Motulbackend.dtos.assistantConversationnel.MessageDto;
import com.binewvision.Motulbackend.services.assistantConversationnel.ConversationService;
import lombok.AllArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/conversations")
@AllArgsConstructor
public class ConversationController {
    
    private final ConversationService conversationService;

    @PostMapping(value = "/find")
    public ResponseEntity<?> findAll(@RequestBody ConversationDto filter) {
        try {
            Page<ConversationDto> pages = conversationService.findAll(filter);

            // 🎯 FIXATION : On construit un schéma de réponse stable et explicite
            // Cela évite la sérialisation brute de PageImpl qui cause le crash 500
            Map<String, Object> response = Map.of(
                    "content", pages.getContent(),
                    "totalElements", pages.getTotalElements(),
                    "totalPages", pages.getTotalPages(),
                    "size", pages.getSize(),
                    "number", pages.getNumber()
            );

            return new ResponseEntity<>(response, HttpStatus.OK);
        } catch (Exception e) {
            return new ResponseEntity<>(Map.of("error", e.getMessage()), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @GetMapping(value = "/get/{id}")
    public ResponseEntity<ConversationDto> findById(@PathVariable("id") Long id) {
        ConversationDto list = conversationService.findById(id);
        return new ResponseEntity<>(list, HttpStatus.OK);
    }


    @GetMapping(value = "/delete/{id}")
    public ResponseEntity<Boolean> delete(@PathVariable("id") Long id) {
        conversationService.delete(id);
        return new ResponseEntity<>(true, HttpStatus.OK);
    }

    @PostMapping(value = "/send")
    public ResponseEntity<MessageDto> sendMessage(@RequestBody MessageDto object) {
        object = conversationService.sendMessage(object);
        return new ResponseEntity<>(object, HttpStatus.OK);
    }

    @PostMapping("/rename")
    public ResponseEntity<ConversationDto> renameConversation(@RequestBody ConversationDto conversation) {
        conversation = conversationService.renameConversation(conversation);
        return new ResponseEntity<>(conversation, HttpStatus.OK);
    }

}
