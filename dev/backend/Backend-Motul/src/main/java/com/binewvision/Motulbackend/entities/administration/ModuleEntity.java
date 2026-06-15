package com.binewvision.Motulbackend.entities.administration;


import jakarta.persistence.Entity;
import jakarta.persistence.EntityListeners;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
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
@Table(name = "module")
@EntityListeners(AuditingEntityListener.class)
public class ModuleEntity {

    @Id
    private Long code;
    private String libelle;
    private int ordre;

}
