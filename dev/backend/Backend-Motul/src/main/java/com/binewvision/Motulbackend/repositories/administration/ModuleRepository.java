package com.binewvision.Motulbackend.repositories.administration;

import com.binewvision.Motulbackend.entities.administration.ModuleEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

import java.util.List;


public interface ModuleRepository extends JpaRepository<ModuleEntity, String>, JpaSpecificationExecutor<ModuleEntity> {
    List<ModuleEntity> findAllByOrderByOrdre();
}
