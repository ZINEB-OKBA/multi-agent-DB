package com.binewvision.Motulbackend.services.Document;

import com.binewvision.Motulbackend.configuration.ApplicationProperties;
import com.binewvision.Motulbackend.entities.Document.Document;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

@Slf4j
@Service
@RequiredArgsConstructor
public class FileIndexerExecutor {

    private final ApplicationProperties applicationProperties;
    private final RestTemplate restTemplate = new RestTemplate();

    @Async // 🚀 Cette méthode s'exécute en tâche de fond instantanée !
    public void triggerInstantIndexing(Document doc) {
        try {
            log.info("⚡ Déclenchement instantané de l'indexation pour : {}", doc.getFileName());

            // 1. Récupérer l'URL Python de ton application.yml
            String fastapiUrl = applicationProperties.getExternalAiConfig().getDocuments();

            // 2. Préparer les données pour Python
            var payload = new Object() {
                public final Long documentId = doc.getId();
                public final String fileName = doc.getFileName();
                public final String content = doc.getContent(); // Le Base64 TEXT pur et complet !
                public final Long projectId = doc.getProject().getId();
            };

            // 3. Envoyer la requête POST à FastAPI
            restTemplate.postForEntity(fastapiUrl, payload, String.class);
            log.info("✅ Signal d'indexation envoyé à Python pour {}", doc.getFileName());

        } catch (Exception e) {
            log.error("❌ Impossible de contacter le serveur IA pour {} : {}", doc.getFileName(), e.getMessage());
        }
    }
}