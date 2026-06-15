package com.binewvision.Motulbackend.entities.airflow_data;


import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDate;
import java.time.LocalTime;

@Getter
@Setter
@Entity
@NoArgsConstructor
@AllArgsConstructor
@Table(name = "bande_fluctuations", schema = "public")
public class BandeFluctuationsEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "devises", nullable = false)
    private String devises;

    @Column(name = "heure", nullable = false)
    private LocalTime heure;

    @Column(name = "cours_minimum", nullable = false)
    private Double coursMinimum;

    @Column(name = "cours_maximum", nullable = false)
    private Double coursMaximum;

    @Column(name = "scraping_date", nullable = false)
    private LocalDate scrapingDate;

}
