package com.binewvision.Motulbackend.entities.airflow_data;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Getter
@Setter
@Entity
@NoArgsConstructor
@AllArgsConstructor
@Table(name = "asfim", schema = "public")
public class AsfimEntity {

    @Id
    @Column(name = "id", nullable = false)
    private Long id;

    @Column(name = "url")
    private String url;

    @Column(name = "nom_fichier")
    private String nomFichier;

    @Column(name = "categorie")
    private String categorie;

    @Column(name = "date_publication")
    private LocalDate datePublication;

    @Column(name = "date_extraction")
    private LocalDateTime dateExtraction;
}
