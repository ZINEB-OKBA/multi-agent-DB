package com.binewvision.Motulbackend.entities.administration;


import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

@Entity
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@Table(name = "role")
@EntityListeners(AuditingEntityListener.class)
public class RoleEntity {

    @Id
    private String identifiant;
    private String description;
    private String libelle;

    @ManyToOne
    @JoinColumn(name = "module")
    private ModuleEntity module;

}
