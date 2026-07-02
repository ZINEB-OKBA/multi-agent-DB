package com.binewvision.Motulbackend.services.assistantConversationnel.impls;

import com.binewvision.Motulbackend.configuration.ApplicationProperties;
import com.binewvision.Motulbackend.dtos.assistantConversationnel.MessageDto;
import com.binewvision.Motulbackend.entities.Project.Project;
import com.binewvision.Motulbackend.repositories.Project.Projectrepository;
import com.binewvision.Motulbackend.services.assistantConversationnel.AiService;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class AiServiceImpl implements AiService {

    private static final Logger logger = LoggerFactory.getLogger(AiServiceImpl.class);

    private final RestTemplate restTemplate = new RestTemplate();
    private final ApplicationProperties applicationProperties;
    private final Projectrepository projectRepository;

    @Override
    public List<Map<String, Object>> getAllProjects() {
        // Va chercher les vrais projets en BDD PostgreSQL triés par date
        List<Project> projects = projectRepository.findAllByOrderByCreatedAtDesc();

        // Transforme en List<Map> pour correspondre à Angular et au contrôleur
        return projects.stream().map(p -> Map.of(
                "name", (Object) p.getName(),
                "description", p.getDescription() != null ? p.getDescription() : "Aucune description disponible."
        )).collect(Collectors.toList());
    }

    @Override
    public Map<String, Object> askQuestion(String project, Map<String, Object> payload) {
        // applicationProperties.getExternalAiConfig().getUrl() doit pointer vers : http://localhost:8000/api/chat/message
        String url = applicationProperties.getExternalAiConfig().getUrl();

        logger.info("📡 Appel REST vers FastAPI — URL: {} | Projet ciblé: {}", url, project);
        return restTemplate.postForObject(url, payload, Map.class);
    }

    @Override
    public Map<String, Object> askQuestion(MessageDto messageDto) {
        String url = applicationProperties.getExternalAiConfig().getUrl();
        logger.info("📡 Appel REST direct via MessageDto vers FastAPI — URL: {}", url);
        return restTemplate.postForObject(url, messageDto, Map.class);
    }

    @Override
    public Map<String, Object> createProject(Map<String, Object> projectData) { return Map.of(); }

    @Override
    public void deleteProject(String projectName) {}

    @Override
    public Map<String, Object> indexDocuments(String project) { return Map.of(); }

    @Override
    public List<Map<String, Object>> getDocuments(String project) { return List.of(); }
}