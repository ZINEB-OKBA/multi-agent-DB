package com.binewvision.Motulbackend.dtos;

import com.fasterxml.jackson.annotation.JsonInclude;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

public class Projectdto {

    // ── Requête création projet ───────────────────────────────────────────────
    @Data
    @Builder
    @NoArgsConstructor  // ✨ Ajouté pour permettre à Jackson de lire le JSON d'Angular
    @AllArgsConstructor // ✨ Ajouté pour que @Builder fonctionne avec NoArgsConstructor
    public static class CreateRequest {
        @NotBlank(message = "Le nom du projet est obligatoire")
        @Size(min = 2, max = 100, message = "Le nom doit faire entre 2 et 100 caractères")
        private String name;

        @Size(max = 500, message = "La description ne peut pas dépasser 500 caractères")
        private String description;
    }

    // ── Réponse complète projet ───────────────────────────────────────────────
    @Data
    @Builder
    @NoArgsConstructor  // ✨ Ajouté
    @AllArgsConstructor // ✨ Ajouté
    @JsonInclude(JsonInclude.Include.NON_NULL)
    public static class Response {
        private Long          id;
        private String        name;
        private String        description;
        private LocalDateTime createdAt;
        private LocalDateTime updatedAt;

        private int  totalDocuments;
        private int  pdfCount;
        private int  excelCount;
        private int  indexedCount;
        private int  pendingCount;

        private List<Documentdto.Response> documents;
    }

    // ── Réponse légère (Summary) ──────────────────────────────────────────────
    @Data
    @Builder
    @NoArgsConstructor  // ✨ Ajouté
    @AllArgsConstructor // ✨ Ajouté
    public static class Summary {
        private Long          id;
        private String        name;
        private String        description;
        private LocalDateTime createdAt;
        private int           totalDocuments;
        private int           indexedCount;
    }
}