package com.binewvision.Motulbackend.services.administration;

import com.binewvision.Motulbackend.dtos.administration.ModuleDto;
import com.binewvision.Motulbackend.dtos.administration.ProfileDto;
import com.binewvision.Motulbackend.dtos.administration.RoleDto;
import org.springframework.data.domain.Page;

import java.util.List;

public interface ProfileService {
    Page<ProfileDto> findAll(ProfileDto filter);
    ProfileDto findById(Long id);
    ProfileDto save(ProfileDto object);
    void delete(Long id);
    List<RoleDto> getCurrentUserRoles();
    List<ModuleDto> getModules();
    List<RoleDto> getRolesByModules(ModuleDto module);
}
