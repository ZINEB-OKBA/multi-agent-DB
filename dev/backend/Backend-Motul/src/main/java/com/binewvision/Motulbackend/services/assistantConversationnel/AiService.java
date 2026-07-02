package com.binewvision.Motulbackend.services.assistantConversationnel;

import com.binewvision.Motulbackend.dtos.assistantConversationnel.MessageDto;
import java.util.List;
import java.util.Map;

public interface AiService {
    // 🎯 Ajoute cette ligne si elle est absente pour autoriser la signature à 2 paramètres
    Map<String, Object> askQuestion(String project, Map<String, Object> payload);

    Map<String, Object> askQuestion(MessageDto messageDto);
    List<Map<String, Object>> getAllProjects();
    Map<String, Object> createProject(Map<String, Object> projectData);
    void deleteProject(String projectName);
    Map<String, Object> indexDocuments(String project);
    List<Map<String, Object>> getDocuments(String project);
}