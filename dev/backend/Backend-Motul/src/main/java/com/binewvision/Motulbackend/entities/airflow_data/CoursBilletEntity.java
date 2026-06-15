package com.binewvision.Motulbackend.entities.airflow_data;


import jakarta.persistence.*;
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
@Table(name = "cours_billet", schema = "public")
public class CoursBilletEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "devises", nullable = false)
    private String devises;

    @Column(name = "achat_clientele", nullable = false)
    private Double achatClientele;

    @Column(name = "vente_clientele", nullable = false)
    private Double venteClientele;

    @Column(name = "scraping_date", nullable = false)
    private LocalDate scrapingDate;

}
