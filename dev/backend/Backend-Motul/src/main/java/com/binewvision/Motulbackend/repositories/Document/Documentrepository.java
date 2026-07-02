package com.binewvision.Motulbackend.repositories.Document;

import com.binewvision.Motulbackend.entities.Document.Document;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface Documentrepository extends JpaRepository<Document, Long> {

    /** Tous les documents d'un projet, triés par date d'upload. */
    List<Document> findByProjectIdOrderByUploadedAtDesc(Long projectId);

    /** Vérifie si un fichier existe déjà dans un projet (évite les doublons). */
    boolean existsByProjectIdAndFileName(Long projectId, String fileName);

    /** Cherche un document par nom dans un projet précis. */
    Optional<Document> findByProjectIdAndFileName(Long projectId, String fileName);

    /** Documents non encore indexés dans un projet (Recherche simplifiée sans fileType). */
    List<Document> findByProjectIdAndIsIndexedFalse(Long projectId);

    /** Compte les documents indexés d'un projet. */
    long countByProjectIdAndIsIndexedTrue(Long projectId);

    /** Compte tous les documents d'un projet. */
    long countByProjectId(Long projectId);

    /**
     * Met à jour le statut d'indexation directement en base.
     */
    @Modifying
    @Query("""
        UPDATE Document d SET
            d.isIndexed  = :indexed,
            d.indexing   = false,
            d.indexError = :error,
            d.indexedAt  = :indexedAt
        WHERE d.id = :id
    """)
    void updateIndexStatus(
            @Param("id")        Long id,
            @Param("indexed")   boolean indexed,
            @Param("error")     String error,
            @Param("indexedAt") LocalDateTime indexedAt
    );

    /**
     * Réinitialise le flag "indexing" (sécurité au démarrage de l'app).
     */
    @Modifying
    @Query("UPDATE Document d SET d.indexing = false WHERE d.indexing = true")
    void resetStuckIndexing();
}