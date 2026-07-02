package com.binewvision.Motulbackend.dtos.administration;


import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class RoleDto {
    private String description;
    private String libelle;
    private String identifiant;
    private ModuleDto module;
}
