package com.binewvision.Motulbackend.dtos;
import com.fasterxml.jackson.annotation.JsonProperty; // 📥 Pense à vérifier cet import en haut du fichier !
import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

public class Documentdto {

    // Nouveau DTO pour la réception de la requête
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class Request {
        private String fileName;
        private Long projectId;      // Pour faire le lien OneToMany avec le Projet
        private String content; //'EST ICI que le Front-end va envoyer le Base64 !

    }

    @Data @Builder
    @JsonInclude(JsonInclude.Include.NON_NULL)
    public static class Response {
        private Long          id;
        private String        fileName;
        private Long          projectId;
        private String        projectName;
        private Boolean       isIndexed;
        private Boolean       indexing;
        private LocalDateTime indexedAt;
        private String        indexError;
        private LocalDateTime uploadedAt;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class IndexCallback {

        @JsonProperty("documentId") // 🎯 Force la liaison avec la clé JSON exacte de Python
        private Long documentId;

        @JsonProperty("success")
        private boolean success;

        @JsonProperty("error")
        private String error;

        @JsonProperty("chunks")
        private Integer chunks;
    }

    @Data @Builder
    public static class IndexRequest {
        private Long   documentId;
        private String projectName;
        private String callbackUrl;
    }
}