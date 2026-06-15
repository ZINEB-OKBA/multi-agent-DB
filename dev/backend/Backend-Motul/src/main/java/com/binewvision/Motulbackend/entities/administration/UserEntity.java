package com.binewvision.Motulbackend.entities.administration;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.experimental.SuperBuilder;
import org.springframework.data.annotation.CreatedBy;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedBy;
import org.springframework.data.annotation.LastModifiedDate;

import java.time.LocalDateTime;


@Getter
@Setter
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@Table(name = "users")
@Entity
public class UserEntity {

    @Id
    @SequenceGenerator(initialValue=1, name="user_seq", sequenceName="user_sequence", allocationSize=1)
    @GeneratedValue(strategy=GenerationType.SEQUENCE, generator="user_seq")
    private Long id;

    private String firstName;
    private String lastName;

    private String email;
    private String password;

    private String phone;
    private byte[] image;
    private String address;

    private boolean deleted;

    private boolean enabled;
    private boolean locked;

    @CreatedDate
    @Column( updatable=false )
    private LocalDateTime createdAt;

    @CreatedBy
    @Column( updatable=false )
    private String createdBy;

    @LastModifiedDate
    private LocalDateTime updatedOn;

    @LastModifiedBy
    private String updatedBy;

    @ManyToOne
    @JoinColumn(name = "profile")
    private ProfileEntity profile;

    @ManyToOne
    @JoinColumn(name = "service")
    private ListeEntity service;

    public void setImage(Object image) {
        if(image instanceof String){
            this.image = ((String) image).getBytes();
        }else {
            this.image = (byte[]) image;
        }
    }


}
