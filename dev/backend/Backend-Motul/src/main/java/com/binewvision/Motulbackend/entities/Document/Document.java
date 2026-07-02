package com.binewvision.Motulbackend.entities.Document;


import com.binewvision.Motulbackend.entities.Project.Project;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;

import java.sql.Types;
import java.time.LocalDateTime;

@Entity
@Table(name = "documents")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class Document {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /** Nom original du fichier (ex: rapport_2024.pdf) */
    @Column(nullable = false, length = 255)
    private String fileName;


    @Column(name = "content", columnDefinition = "TEXT")
    @JdbcTypeCode(Types.LONGVARCHAR) // 🎯 Force Hibernate à envoyer le texte brut et non un OID pointer
    private String content;
    // ── Statut d'indexation FAISS ─────────────────────────────────────────────

    /**
     * false  = pas encore indexé (état initial après upload)
     * true   = indexé avec succès dans FAISS
     */
    @Column(nullable = false)
    @Builder.Default
    private Boolean isIndexed = false;

    /**
     * true   = indexation en cours en ce moment (lancée par Python)
     * false  = pas en cours
     */
    @Column(nullable = false)
    @Builder.Default
    private Boolean indexing = false;

    /** Date/heure de la dernière indexation réussie */
    private LocalDateTime indexedAt;

    /** Message d'erreur si la dernière indexation a échoué */
    @Column(length = 1000)
    private String indexError;

    @CreationTimestamp
    @Column(updatable = false)
    private LocalDateTime uploadedAt;

    // ── Relation ──────────────────────────────────────────────────────────────

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "project_id", nullable = false)
    private Project project;

    // ── Helpers ───────────────────────────────────────────────────────────────

    /** Marque le document comme indexé avec succès. */
    public void markIndexed() {
        this.isIndexed  = true;
        this.indexing   = false;
        this.indexError = null;
        this.indexedAt  = LocalDateTime.now();
    }

    /** Marque le document comme en cours d'indexation. */
    public void markIndexing() {
        this.indexing   = true;
        this.indexError = null;
    }

    /** Marque le document comme échoué à l'indexation. */
    public void markIndexFailed(String error) {
        this.indexing   = false;
        this.isIndexed  = false;
        this.indexError = error;
    }

    /** Réinitialise le statut (ex: après un re-upload). */
    public void resetIndexStatus() {
        this.isIndexed  = false;
        this.indexing   = false;
        this.indexedAt  = null;
        this.indexError = null;
    }
    public Boolean getIndexed() {
        return this.isIndexed;
    }

    public void setIndexed(boolean indexed) {
        this.isIndexed = indexed;
    }
}