package com.binewvision.Motulbackend.services.Document;

import com.binewvision.Motulbackend.configuration.ApplicationProperties;
import com.binewvision.Motulbackend.dtos.Documentdto;
import com.binewvision.Motulbackend.entities.Document.Document;
import com.binewvision.Motulbackend.entities.Project.Project;
import com.binewvision.Motulbackend.repositories.Document.Documentrepository; // À adapter selon ton package exact
import com.binewvision.Motulbackend.repositories.Project.Projectrepository;       // À adapter selon ton projet
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class Documentservice {
    private final FileIndexerExecutor fileIndexerExecutor;
    private final Documentrepository documentRepository;
    private final Projectrepository projectRepository;

    // On injecte ta classe de configuration globale
    private final ApplicationProperties applicationProperties;

    /**
     * 1. Reçoit le fichier en Base64 du Front-end, le valide et le sauvegarde dans PostgreSQL.
     */
    @Transactional
    public void saveDocument(Documentdto.Request request) {
        String base64FileContent = request.getContent();

        // --- ÉTAPE A : VALIDATION DU FORMAT (PDF, Word, Excel, CSV) ---
        // --- ÉTAPE A : VALIDATION DU FORMAT (PDF, Word, Excel, CSV) ---
        if (base64FileContent == null || !base64FileContent.startsWith("data:")) {
            throw new IllegalArgumentException("Le fichier n'est pas au format Base64 valide (doit commencer par 'data:')");
        }

        // 🎯 Sécurisation par extension : beaucoup plus fiable que le Type MIME instable des navigateurs
        String fileNameLower = request.getFileName().toLowerCase();
        boolean isAllowedExtension = fileNameLower.endsWith(".pdf")
                || fileNameLower.endsWith(".docx")
                || fileNameLower.endsWith(".doc")
                || fileNameLower.endsWith(".xlsx")
                || fileNameLower.endsWith(".xls")
                || fileNameLower.endsWith(".csv");

        if (!isAllowedExtension) {
            throw new IllegalArgumentException("Ce format de fichier n'est pas autorisé pour le fichier : " + request.getFileName());
        }
        // --- ÉTAPE B : VALIDATION DE LA TAILLE ---
        String base64ContentPure = base64FileContent.substring(base64FileContent.indexOf(",") + 1);
        long sizeInBytes = (base64ContentPure.length() * 3L) / 4L;

        // On utilise la méthode 'getMaxUpload()' que ton amie a écrite dans ton UploadConfig !
        long maxUploadBytes = applicationProperties.getUploadConfig().getMaxUpload();

        if (sizeInBytes > maxUploadBytes) {
            throw new IllegalArgumentException("Le fichier est trop lourd pour le serveur !");
        }

        // --- ÉTAPE C : LIEN RELATIONNEL ET DOUBLONS ---
        Project project = projectRepository.findById(request.getProjectId())
                .orElseThrow(() -> new RuntimeException("Projet introuvable avec l'ID : " + request.getProjectId()));

        if (documentRepository.existsByProjectIdAndFileName(request.getProjectId(), request.getFileName())) {
            throw new IllegalArgumentException("Un fichier nommé '" + request.getFileName() + "' existe déjà dans ce projet.");
        }

        // --- ÉTAPE D : ENREGISTREMENT ---
        Document document = new Document();
        document.setFileName(request.getFileName());
        document.setContent(base64FileContent);
        document.setUploadedAt(LocalDateTime.now());
        document.setProject(project);

        document.setIndexed(false);
        document.setIndexing(true); // 🎯 On le passe directement à TRUE car l'indexation démarre de suite !

        // Sauvegarde en BDD
        document = documentRepository.save(document);

        // 🔥 LE COMMUTATEUR INSTANTANÉ : On lance l'IA immédiatement en tâche de fond !
        fileIndexerExecutor.triggerInstantIndexing(document);
    }

    /**
     * 2. Récupère tous les documents d'un projet donnés, triés du plus récent au plus ancien.
     */
    @Transactional(readOnly = true)
    public List<Documentdto.Response> getProjectDocuments(Long projectId) {
        List<Document> documents = documentRepository.findByProjectIdOrderByUploadedAtDesc(projectId);
        return documents.stream().map(this::convertToResponseDto).collect(Collectors.toList());
    }

    /**
     * 3. Récupère les informations et l'état actuel d'un seul document.
     */
    @Transactional(readOnly = true)
    public Documentdto.Response getDocumentStatus(Long documentId) {
        Document document = documentRepository.findById(documentId)
                .orElseThrow(() -> new RuntimeException("Document introuvable avec l'ID : " + documentId));
        return convertToResponseDto(document);
    }

    /**
     * 4. Déclenche l'état de préparation à l'indexation pour l'IA.
     */
    @Transactional
    public Documentdto.Response triggerIndexing(Long documentId) {
        Document document = documentRepository.findById(documentId)
                .orElseThrow(() -> new RuntimeException("Document introuvable"));

        document.markIndexing();
        Document updatedDocument = documentRepository.save(document);
        return convertToResponseDto(updatedDocument);
    }

    /**
     * 5. Passe tous les documents non indexés d'un projet en mode "En cours d'indexation".
     */
    @Transactional
    public List<Documentdto.Response> triggerProjectIndexing(Long projectId) {
        List<Document> pendingDocuments = documentRepository.findByProjectIdAndIsIndexedFalse(projectId);
        for (Document doc : pendingDocuments) {
            doc.markIndexing();
        }
        List<Document> updatedDocs = documentRepository.saveAll(pendingDocuments);
        return updatedDocs.stream().map(this::convertToResponseDto).collect(Collectors.toList());
    }

    /**
     * 6. Reçoit la réponse de l'IA (Callback) pour mettre à jour les statuts.
     */
    @Transactional
    public void handleIndexCallback(Documentdto.IndexCallback callback) {
        LocalDateTime indexedAtTime = callback.isSuccess() ? LocalDateTime.now() : null;
        String errorMessage = callback.isSuccess() ? null : callback.getError();

        documentRepository.updateIndexStatus(
                callback.getDocumentId(),
                callback.isSuccess(),
                errorMessage,
                indexedAtTime
        );
    }

    /**
     * 7. Supprime un document de PostgreSQL.
     */
    @Transactional
    public void deleteDocument(Long documentId) {
        if (!documentRepository.existsById(documentId)) {
            throw new RuntimeException("Impossible de supprimer : Document inexistant");
        }
        documentRepository.deleteById(documentId);
    }

    /**
     * Mapping : Entité -> DTO Response via Builder
     */
    private Documentdto.Response convertToResponseDto(Document document) {
        return Documentdto.Response.builder()
                .id(document.getId())
                .fileName(document.getFileName())
                .projectId(document.getProject() != null ? document.getProject().getId() : null)
                .projectName(document.getProject() != null ? document.getProject().getName() : null)
                .isIndexed(document.getIndexed())
                .indexing(document.getIndexing())
                .indexedAt(document.getIndexedAt())
                .indexError(document.getIndexError())
                .uploadedAt(document.getUploadedAt())
                .build();
    }

    /**
     * Récupère l'entité Document brute pour le téléchargement.
     */
    @Transactional(readOnly = true)
    public Document findById(Long documentId) {
        return documentRepository.findById(documentId)
                .orElseThrow(() -> new RuntimeException("Document introuvable avec l'ID : " + documentId));
    }
}