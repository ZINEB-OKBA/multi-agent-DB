package com.binewvision.Motulbackend.entities.administration;

import com.binewvision.Motulbackend.entities.BaseEntity;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@Entity
@NoArgsConstructor
@AllArgsConstructor
@Table(name = "listes")
public class ListeEntity extends BaseEntity {

    @Id
    @SequenceGenerator(initialValue=1, name="liste_seq", sequenceName="liste_sequence", allocationSize=1)
    @GeneratedValue(strategy=GenerationType.SEQUENCE, generator="liste_seq")
    private Long id;

    private String label;
    private String value;

    private String nature;
    private boolean deleted;

    @ManyToOne
    @JoinColumn(name = "parent")
    private ListeEntity parent;

}
