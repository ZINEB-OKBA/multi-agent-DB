package com.binewvision.Motulbackend.entities.administration;


import com.binewvision.Motulbackend.entities.BaseEntity;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.util.List;

@Getter
@Setter
@Entity
@NoArgsConstructor
@AllArgsConstructor
@Table(name = "profiles")
@EntityListeners(AuditingEntityListener.class)
public class ProfileEntity extends BaseEntity {

    @Id
    @SequenceGenerator(initialValue=1, name="profile_seq", sequenceName="profile_sequence", allocationSize=1)
    @GeneratedValue(strategy=GenerationType.SEQUENCE, generator="profile_seq")
    private Long id;
    private String name;

    @ManyToMany(fetch = FetchType.EAGER)
    @JoinTable(
            name = "profil_roles",
            joinColumns = @JoinColumn(name = "profil"),
            inverseJoinColumns = @JoinColumn(name = "roles")
    )
    private List<RoleEntity> roles;
}
