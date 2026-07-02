package com.binewvision.Motulbackend.controllers.assistantConversationnel;

import com.binewvision.Motulbackend.services.assistantConversationnel.AiService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class AiController {

    private final AiService aiService;

    // --- Gestion du Chat ---
//    @PostMapping("/chat/{project}")
//    public Map<String, Object> chat(@PathVariable String project, @RequestBody Map<String, Object> payload) {
//        // On passe directement le projet et le body (question, etc.)
//        return aiService.askQuestion(project, payload);
//    }
//
//    // --- Gestion des Projets ---
//    @GetMapping("/projects")
//    public List<Map<String, Object>> listProjects() {
//        return aiService.getAllProjects();
//    }
//
//    @PostMapping("/projects")
//    public Map<String, Object> createProject(@RequestBody Map<String, Object> body) {
//        return aiService.createProject(body);
//    }
//
//    @DeleteMapping("/projects/{name}")
//    public void deleteProject(@PathVariable String name) {
//        aiService.deleteProject(name);
//    }
//
//    // --- Gestion des Documents ---
//    @PostMapping("/documents/{project}/index")
//    public Map<String, Object> index(@PathVariable String project) {
//        return aiService.indexDocuments(project);
//    }
//
//    @GetMapping("/documents/{project}")
//    public List<Map<String, Object>> getDocs(@PathVariable String project) {
//        return aiService.getDocuments(project);
//    }
}