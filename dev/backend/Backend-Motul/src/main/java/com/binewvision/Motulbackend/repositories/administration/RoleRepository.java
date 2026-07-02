package com.binewvision.Motulbackend.repositories.administration;

import com.binewvision.Motulbackend.entities.administration.ModuleEntity;
import com.binewvision.Motulbackend.entities.administration.RoleEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

import java.util.List;


public interface RoleRepository extends JpaRepository<RoleEntity, String>, JpaSpecificationExecutor<RoleEntity> {

    List<RoleEntity> findAllByModule(ModuleEntity module);

}
