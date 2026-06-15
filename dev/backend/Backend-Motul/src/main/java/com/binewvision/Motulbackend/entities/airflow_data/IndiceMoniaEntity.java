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
@Table(name = "indice_monia", schema = "public")
public class IndiceMoniaEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "indice_monia", nullable = false, columnDefinition = "text")
    private String indiceMonia;

    @Column(name = "volume_jj", nullable = false)
    private Double volumeJj;

    @Column(name = "date_reference")
    private LocalDate dateReference;

    @Column(name = "date_publication", nullable = false)
    private LocalDate datePublication;

}