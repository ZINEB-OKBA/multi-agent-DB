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
@Table(name = "marche_monetaire", schema = "public")
public class MarcheMonetaireEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "date", nullable = false)
    private LocalDate date;

    @Column(name = "taux_moyen_pondere")
    private Double tauxMoyenPondere;

    @Column(name = "volume_jj")
    private Double volumeJj;

    @Column(name = "encours")
    private Double encours;

}