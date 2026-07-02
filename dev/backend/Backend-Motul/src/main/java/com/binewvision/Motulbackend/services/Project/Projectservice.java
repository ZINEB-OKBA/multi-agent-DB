package com.binewvision.Motulbackend.services.Project;


import com.binewvision.Motulbackend.dtos.Projectdto;
import com.binewvision.Motulbackend.entities.Document.Document;
import com.binewvision.Motulbackend.entities.Project.Project;
import com.binewvision.Motulbackend.repositories.Project.Projectrepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class Projectservice {

    private final Projectrepository projectRepository;

    // ── Création ──────────────────────────────────────────────────────────────

    @Transactional
    public Projectdto.Response create(Projectdto.CreateRequest req) {
        if (projectRepository.existsByName(req.getName())) {
            throw new IllegalArgumentException(
                    "Un projet avec le nom '" + req.getName() + "' existe déjà."
            );
        }

        Project project = Project.builder()
                .name(req.getName().trim())
                .description(req.getDescription() != null ? req.getDescription().trim() : null)
                .build();

        project = projectRepository.save(project);
        log.info("✅ Projet créé : {} (id={})", project.getName(), project.getId());
        return toResponse(project, false);
    }

    // ── Lecture ───────────────────────────────────────────────────────────────

    @Transactional(readOnly = true)
    public List<Projectdto.Summary> listAll() {
        return projectRepository.findAllByOrderByCreatedAtDesc()
                .stream()
                .map(this::toSummary)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public Projectdto.Response getById(Long id) {
        Project project = findOrThrow(id);
        return toResponse(project, true);   // true = inclure la liste des documents
    }

    @Transactional(readOnly = true)
    public Project findOrThrow(Long id) {
        return projectRepository.findById(id)
                .orElseThrow(() -> new jakarta.persistence.EntityNotFoundException(
                        "Projet introuvable : id=" + id
                ));
    }

    // ── Suppression ───────────────────────────────────────────────────────────

    @Transactional
    public void delete(Long id) {
        Project project = findOrThrow(id);
        projectRepository.delete(project);
        log.info("🗑️ Projet supprimé : {} (id={})", project.getName(), id);
    }

    // ── Mappers Sécurisés contre les listes nulles ───────────────────────────────

    private Projectdto.Response toResponse(Project p, boolean includeDocuments) {
        // ✨ Sécurisation : Si getDocuments() est null, on prend une liste vide
        List<Document> docs = p.getDocuments() != null ? p.getDocuments() : List.of();

        long indexedCount = docs.stream().filter(d -> d.getIsIndexed() != null && d.getIsIndexed()).count();
        long pendingCount = docs.stream().filter(d -> d.getIsIndexed() == null || !d.getIsIndexed()).count();

        var builder = Projectdto.Response.builder()
                .id(p.getId())
                .name(p.getName())
                .description(p.getDescription())
                .createdAt(p.getCreatedAt())
                .updatedAt(p.getUpdatedAt())
                .totalDocuments(docs.size())
                .indexedCount((int) indexedCount)
                .pendingCount((int) pendingCount);

        if (includeDocuments && p.getDocuments() != null) {
            builder.documents(
                    docs.stream().map(this::docToResponse).collect(Collectors.toList())
            );
        }

        return builder.build();
    }

    private Projectdto.Summary toSummary(Project p) {
        List<Document> docs = p.getDocuments() != null ? p.getDocuments() : List.of();
        long indexed = docs.stream().filter(d -> d.getIsIndexed() != null && d.getIsIndexed()).count();

        return Projectdto.Summary.builder()
                .id(p.getId())
                .name(p.getName())
                .description(p.getDescription())
                // ✨ Sécurisation : Si la date est nulle en BDD, on met l'heure actuelle pour éviter le crash 500
                .createdAt(p.getCreatedAt() != null ? p.getCreatedAt() : java.time.LocalDateTime.now())                .totalDocuments(docs.size())
                .indexedCount((int) indexed)
                .build();
    }

    private com.binewvision.Motulbackend.dtos.Documentdto.Response docToResponse(Document d) {
        return com.binewvision.Motulbackend.dtos.Documentdto.Response.builder()
                .id(d.getId())
                .fileName(d.getFileName())
                .projectId(d.getProject().getId())
                .projectName(d.getProject().getName())
                .isIndexed(d.getIsIndexed())
                .indexing(d.getIndexing())
                .indexedAt(d.getIndexedAt())
                .indexError(d.getIndexError())
                .uploadedAt(d.getUploadedAt())
                .build();
    }}