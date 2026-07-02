package com.binewvision.Motulbackend.repositories.administration;

import com.binewvision.Motulbackend.entities.administration.ListeEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ListRepository extends JpaRepository<ListeEntity,Long>, JpaSpecificationExecutor<ListeEntity> {

    List<ListeEntity> findByNatureAndDeletedOrderByLabelAsc(String nature, boolean deleted);

    boolean existsByLabelAndDeleted(String label, boolean deleted);
}
