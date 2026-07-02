package com.binewvision.Motulbackend.entities;

import jakarta.persistence.Column;
import jakarta.persistence.MappedSuperclass;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;
import org.springframework.data.annotation.CreatedBy;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedBy;
import org.springframework.data.annotation.LastModifiedDate;

import java.time.LocalDateTime;

@Data
@SuperBuilder
@AllArgsConstructor
@NoArgsConstructor
@MappedSuperclass
public class BaseEntity {

    @CreatedDate
    @Column( updatable=false )
    private LocalDateTime createdOn;

    @CreatedBy
    @Column( updatable=false )
    private String createdBy;

    @LastModifiedDate
    private LocalDateTime updatedOn;

    @LastModifiedBy
    private String updatedBy;

    @Column(name="deleted", columnDefinition="boolean default false")
    private boolean deleted;

}
