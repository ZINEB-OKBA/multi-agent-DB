package com.binewvision.Motulbackend.controllers.Document;

import com.binewvision.Motulbackend.dtos.Documentdto;
import com.binewvision.Motulbackend.entities.Document.Document;
import com.binewvision.Motulbackend.services.Document.Documentservice;
import lombok.RequiredArgsConstructor;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import java.util.Base64;
import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/")
// 🎯 Configuration CORS complète et robuste pour le téléchargement de fichiers binaires
//               @CrossOrigin(
//        origins = "http://localhost:4200",
//        allowedHeaders = "*",
//        methods = {RequestMethod.GET, RequestMethod.POST, RequestMethod.PUT, RequestMethod.DELETE, RequestMethod.OPTIONS},
//        exposedHeaders = "Content-Disposition"
//)
@PreAuthorize("permitAll()")// À sécuriser plus tard selon tes besoins !
public class DocumentController {

    private final Documentservice documentService;

    // --- 1. L'UPLOAD EN BASE64 (Intégré proprement) ---
    @PostMapping("/documents/upload") // Devient automatiquement /api/documents/upload
    public ResponseEntity<String> uploadDocument(@RequestBody Documentdto.Request request) {
        try {
            documentService.saveDocument(request);
            return ResponseEntity.ok("Fichier Base64 validé et stocké avec succès dans PostgreSQL !");
        } catch (IllegalArgumentException e) {
            // Si le fichier est trop lourd ou mauvais format (Erreur gérée par notre logique)
            return ResponseEntity.badRequest().body(e.getMessage());
        } catch (Exception e) {
            // Toute autre erreur inattendue
            return ResponseEntity.internalServerError().body("Erreur lors de l'enregistrement : " + e.getMessage());
        }
    }

    // --- 2. LES MÉTHODES DE TA TEMPLATE (Réparées) ---

    @GetMapping("/projects/{projectId}/documents")
    public ResponseEntity<List<Documentdto.Response>> listDocuments(
            @PathVariable Long projectId
    ) {
        return ResponseEntity.ok(
                documentService.getProjectDocuments(projectId)
        );
    }

    @GetMapping("/documents/{documentId}/status")
    public ResponseEntity<Documentdto.Response> getDocumentStatus(
            @PathVariable Long documentId
    ) {
        return ResponseEntity.ok(
                documentService.getDocumentStatus(documentId)
        );
    }

    @PostMapping("/documents/{documentId}/index")
    public ResponseEntity<Documentdto.Response> indexDocument(
            @PathVariable Long documentId
    ) {
        return ResponseEntity.accepted()
                .body(documentService.triggerIndexing(documentId));
    }

    @PostMapping("/projects/{projectId}/documents/index-all")
    public ResponseEntity<List<Documentdto.Response>> indexAllPending(
            @PathVariable Long projectId
    ) {
        return ResponseEntity.accepted()
                .body(documentService.triggerProjectIndexing(projectId));
    }

    // ✅ Nouvelle configuration alignée sur le script Python :
    @PostMapping("/api/internal/documents/callback")
    public ResponseEntity<Void> handleIndexCallback(
            @RequestBody Documentdto.IndexCallback callback
    ) {
        System.out.println("📞 [SPRING BOOT] Callback IA reçu ! Traitement du document ID: " + callback.getDocumentId());
        documentService.handleIndexCallback(callback);
        System.out.println("✅ [SPRING BOOT] Statut PostgreSQL mis à jour avec succès !");
        return ResponseEntity.ok().build();
    }
    // Retire "/api" pour correspondre au format de tes autres routes de ce controller
    @GetMapping("/documents/{id}/download")
    public ResponseEntity<Resource> downloadDocument(@PathVariable Long id) {
        Document doc = documentService.findById(id);

        String base64Content = doc.getContent();
        if (base64Content == null || base64Content.isEmpty()) {
            return ResponseEntity.noContent().build();
        }

        // 1. Nettoyage du préfixe Data URL si présent (ex: "data:application/vnd...;base64,")
        if (base64Content.contains(",")) {
            base64Content = base64Content.substring(base64Content.indexOf(",") + 1);
        }

        // 2. Nettoyage de sécurité : on supprime tous les sauts de ligne ou espaces invisibles
        base64Content = base64Content.replaceAll("\\s", "");

        try {
            // 3. Décodage sécurisé en tableau de bytes
            byte[] fileBytes = Base64.getDecoder().decode(base64Content);
            ByteArrayResource resource = new ByteArrayResource(fileBytes);

            // 4. Construction des en-têtes HTTP de téléchargement
            return ResponseEntity.ok()
                    .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + doc.getFileName() + "\"")
                    .contentType(MediaType.APPLICATION_OCTET_STREAM)
                    .contentLength(fileBytes.length) // Crucial pour qu'Angular connaisse la taille exacte du Blob
                    .body(resource);

        } catch (IllegalArgumentException e) {
            System.err.println("❌ Erreur de décodage Base64 pour le document ID " + id + " : " + e.getMessage());
            return ResponseEntity.internalServerError().build();
        }
    }
    @DeleteMapping("/documents/{documentId}")
    public ResponseEntity<Void> deleteDocument(
            @PathVariable Long documentId
    ) {
        documentService.deleteDocument(documentId);
        return ResponseEntity.noContent().build();
    }
} // <--- TOUTES les accolades se ferment maintenant ici, à la toute fin de la classe.