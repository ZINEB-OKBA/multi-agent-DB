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

@Getter
@Setter
@Entity
@NoArgsConstructor
@AllArgsConstructor
@Table(name = "ammc_communiques", schema = "public")
public class AmmcEntity {
    @Id
    @Column(name = "id", nullable = false)
    private Long id;

    @Column(name = "date", nullable = false)
    private LocalDate date;

    @Column(name = "url", nullable = false, columnDefinition = "text")
    private String url;

    @Column(name = "titre", nullable = false, columnDefinition = "text")
    private String titre;
}
